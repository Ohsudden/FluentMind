import getpass
import os
import socket

os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")

from langchain_google_genai import ChatGoogleGenerativeAI
import phoenix as px
from phoenix.otel import register
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, format_span_id, get_current_span
import requests
import json
import weaviate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


class PhoenixTracking:
    def __init__(self, app_name: str, launch_ui: bool = False):
        self.app_name = app_name
        self.session = None
        
        ui_port = 6006
        grpc_port = int(os.environ.get("PHOENIX_GRPC_PORT", 4317))

        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0

        phoenix_running = False
        if is_port_in_use(ui_port):
            phoenix_running = True
            print(f"Phoenix UI port ({ui_port}) is already in use. Assuming Phoenix is running.")
        
        if not phoenix_running:
            if is_port_in_use(grpc_port):
                print(f"Phoenix gRPC port ({grpc_port}) is in use. Finding a free port...")
                new_port = grpc_port + 1
                while is_port_in_use(new_port):
                    new_port += 1
                os.environ["PHOENIX_GRPC_PORT"] = str(new_port)
                print(f"Switched Phoenix gRPC port to {new_port}")

            try:
                self.session = px.launch_app(use_temp_dir=False)
            except Exception as e:
                print(f"Warning: Could not launch Phoenix UI: {e}")

        try:
            tracer_provider = register()
        except Exception as e:
            print(f"Warning: Could not register tracer: {e}")
            tracer_provider = trace.get_tracer_provider()

        self.tracer = tracer_provider.get_tracer(__name__)
        self.phoenix_project_name = "RAG_English_Learning"


    def generate_with_single_input(self, prompt: str, role: str = 'user', top_p: float = None, temperature: float = 1.0,
                               max_tokens: int = 500, model: str = "gemini-2.5-pro", family: str = "gemini", **kwargs):
        """Using comprehensive outlook of parameters for LLM generation with Phoenix tracking."""
        with self.tracer.start_as_current_span("llm_generation", openinference_span_kind='llm') as span:
            try:

                span.add_event("Starting LLM generation")
                span.set_attribute("llm.model_name", model)
                span.set_attribute("llm.input_messages.0.role", role)
                span.set_attribute("llm.input_messages.0.content", prompt)
                span.set_attribute("llm.temperature", temperature if temperature else 1.0)
                span.set_attribute("llm.top_p", top_p if top_p else 1.0)
                span.set_attribute("llm.max_tokens", max_tokens)
                
                if top_p is None:
                    top_p = 1.0
                if temperature is None:
                    temperature = 1.0
                
                if family.lower() == 'openai':
                    if not os.environ.get("OPENAI_API_KEY"):
                        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")
                    llm = ChatOpenAI(
                        model=model if "gpt" in model else "gpt-3.5-turbo",
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model_kwargs={"top_p": top_p, **kwargs}
                    )
                elif family.lower() == 'gemini':
                    if "GOOGLE_API_KEY" not in os.environ:
                        raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file or environment.")
                    
                    llm = ChatGoogleGenerativeAI(
                        model=model,
                        temperature=temperature,  
                        max_tokens=max_tokens,
                        timeout=None,
                        max_retries=2,
                    )
                
                if role.lower() == 'system':
                    messages = [SystemMessage(content=prompt)]
                else:
                    messages = [HumanMessage(content=prompt)]
                
                span.add_event("Invoking LLM")
                response = llm.invoke(messages)
                
                total_tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                
                if hasattr(response, 'response_metadata'):
                    usage = response.response_metadata.get('token_usage', {})
                    total_tokens = usage.get('total_tokens', 0)
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                
                span.set_attribute("llm.output_messages.0.role", "assistant")
                span.set_attribute("llm.output_messages.0.content", response.content)
                span.set_attribute("llm.token_count.total", total_tokens)
                span.set_attribute("llm.token_count.prompt", prompt_tokens)
                span.set_attribute("llm.token_count.completion", completion_tokens)
                
                output_dict = {
                    'role': 'assistant',
                    'content': response.content,
                    'total_tokens': total_tokens,
                    'span_id':  format_span_id(span.get_span_context().span_id),
                }
                
                span.add_event("LLM generation completed")
                span.set_status(Status(StatusCode.OK))
                return output_dict
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.add_event("LLM generation failed")
                raise Exception(f"Failed to generate response with LangChain. Error: {e}")
    
    def generate_params_dict(self,
    prompt: str,
    temperature: float = 1.0,
    role: str = 'user',
    top_p: float = 1.0,
    max_tokens: int = 500,
    model: str = "gemini-2.5-pro",
    ) -> dict:
        
        kwargs = {
            "prompt": prompt,
            "role": role,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "model": model
        }
        return kwargs
    
    def hybrid_retrieve(self, query: str, 
                        collection: "weaviate.collections.collection.sync.Collection" , 
                        alpha: float = 0.5,
                        top_k: int = 5
                    ) -> list:
        """Hybrid retrieval with Phoenix tracking."""
        with self.tracer.start_as_current_span("hybrid_retrieval", openinference_span_kind='retriever') as span:
            try:
                span.add_event("Starting hybrid retrieval")
                span.set_attribute("retrieval.query", query)
                span.set_attribute("retrieval.top_k", top_k)
                span.set_attribute("retrieval.alpha", alpha)
                span.set_attribute("retrieval.collection", collection.name if hasattr(collection, 'name') else "unknown")
                
                response = collection.query.hybrid(query=query, limit=top_k, alpha=alpha)
                response_objects = [x.properties for x in response.objects]
                
                span.set_attribute("retrieval.documents.count", len(response_objects))
                for i, doc in enumerate(response_objects[:3]): 
                    span.set_attribute(f"retrieval.documents.{i}.id", i)
                    span.set_attribute(f"retrieval.documents.{i}.content", str(doc)[:200]) 
                    
                span.add_event(f"Retrieved {len(response_objects)} documents")
                span.set_status(Status(StatusCode.OK))
                return response_objects
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise 
    
    def augmented_prompt(self, query: str, 
                              collection: "weaviate.collections.collection.sync.Collection",
                            top_k: int, 
                            retrieve_function: callable,
                            alpha: float = 0.5,
                            use_rag: bool = True,
                            prompt_context: str = "") -> str:
        """Create augmented prompt with RAG context and Phoenix tracking."""
        with self.tracer.start_as_current_span("augmented_prompt_creation") as span:
            try:
                span.add_event("Creating augmented prompt")
                span.set_attribute("rag.use_rag", use_rag)
                span.set_attribute("rag.query", query)
                span.set_attribute("rag.top_k", top_k)
                span.set_attribute("rag.prompt_context", prompt_context)

                if not use_rag:
                    span.add_event("RAG disabled, returning original query")
                    span.set_status(Status(StatusCode.OK))
                    return query
                
                span.add_event("Retrieving documents for augmentation")
                top_k_documents = retrieve_function(query=query, top_k=top_k, collection=collection)
                
                formatted_data = ""
                
                for document in top_k_documents:
                    if 'grammatical_item' in document:
                         document_layout = (
                            f"Grammar Item: {document.get('grammatical_item', 'N/A')}, "
                            f"Level: {document.get('cefr_j_level', 'N/A')}, "
                            f"Sentence Type: {document.get('sentence_type', 'N/A')}"
                        )
                    else:
                        document_layout = (
                            f"Title: {document.get('title', 'N/A')}, Chunk: {document.get('chunk', 'N/A')}, "
                            f"Published at: {document.get('pubDate', 'N/A')}\nURL: {document.get('link', 'N/A')}"
                        )
                    formatted_data += document_layout + "\n"
                
                retrieve_data_formatted = formatted_data  
                prompt = (
                    f"Prompt Context:{prompt_context}\n"
                    f"Query: {query}\n"
                    f"Context Information: {retrieve_data_formatted}"
                )
                
                span.set_attribute("rag.augmented_prompt_length", len(prompt))
                span.set_attribute("rag.documents_used", len(top_k_documents))
                span.add_event("Augmented prompt created successfully")
                span.set_status(Status(StatusCode.OK))
                return prompt
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise
    

    def generate(self, temperature, top_p, max_tokens, model, prompt_context="", name="English Exam", type="exam", collection_name="CefrGrammarProfile"):
        """Generate English exam with comprehensive RAG workflow tracking."""
        with self.tracer.start_as_current_span(name, openinference_span_kind='chain') as span:
            try:
                span.add_event("Starting English exam generation")
                span.set_attribute(f"{type}.temperature", temperature)
                span.set_attribute(f"{type}.top_p", top_p)
                span.set_attribute(f"{type}.max_tokens", max_tokens)
                span.set_attribute(f"{type}.model", model)
                span.set_attribute(f"{type}.type", "multiple_choice")
                span.set_attribute(f"{type}.question_count", 5)
                
                span.add_event("Connecting to Weaviate")
                client = weaviate.connect_to_local(host="localhost", port=8080, grpc_port=50051)
                
                span.add_event("Creating augmented prompt")
                augmented_prompt = self.augmented_prompt(
                    query=prompt_context, use_rag=True,
                    collection=client.collections.get(collection_name),
                    top_k=5, retrieve_function=self.hybrid_retrieve)
                
                span.set_attribute(f"{type}.augmented_prompt_length", len(augmented_prompt))
                span.add_event(f"Generating {type} with LLM")
                
                response = self.generate_with_single_input(
                    **self.generate_params_dict(prompt=augmented_prompt, role='user', 
                                               temperature=temperature, top_p=top_p, 
                                               max_tokens=max_tokens, model=model)
                )
                
                span.set_attribute(f"{type}.output_length", len(response['content']))
                span.set_attribute(f"{type}.total_tokens", response.get('total_tokens', 0))
                span.add_event(f"{type.capitalize()} generation completed successfully")
                span.set_status(Status(StatusCode.OK))
                return {"content": response['content'], "run_id": response.get('span_id')}
            
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", e.__class__.__name__)
                span.set_attribute("error.message", str(e))
                span.add_event(f"{type.capitalize()} generation failed")
                raise

            finally:
                try:
                    if 'client' in locals():
                        client.close()
                except Exception:
                    pass
    
    def generate_image(self, prompt: str, model: str = "gemini-3-pro-image-preview", size: str = "1024x1024", n: int =1) -> dict:
        """Generate image with Phoenix tracking."""
        with self.tracer.start_as_current_span("image_generation", openinference_span_kind='llm') as span:
            try:
                span.add_event("Starting image generation")
                span.set_attribute("llm.model_name", model)
                span.set_attribute("llm.input.prompt", prompt)
                span.set_attribute("llm.image.size", size)
                span.set_attribute("llm.image.count", n)
                
                if "GOOGLE_API_KEY" not in os.environ:
                    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file or environment.")
                
                llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=1.0,  
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                )
                
                response = llm.generate_image(prompt=prompt, n=n, size=size)
                
                span.set_attribute("llm.image.generated_count", len(response.data))
                for i, img in enumerate(response.data):
                    span.set_attribute(f"llm.image.url.{i}", img.url)
                
                span.add_event("Image generation completed")
                span.set_status(Status(StatusCode.OK))
                return {"images": [img.url for img in response.data]}
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.add_event("Image generation failed")
                raise Exception(f"Failed to generate image. Error: {e}")
        
            