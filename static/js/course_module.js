document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submit-module-answers');
    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = "Grading...";
            
            const exercises = [];
            const exerciseBoxes = document.querySelectorAll('.exercise-box');
            
            exerciseBoxes.forEach((box, index) => {
                // Get text content of the box as the "question context", excluding inputs
                // Clone the node to remove inputs from text extraction if we wanted to be substantial,
                // but just getting innerText is usually enough context for the LLM.
                const questionText = box.innerText; 
                
                let userAnswer = "";
                
                // Check for text input
                const textInput = box.querySelector('.exercise-input');
                if (textInput) {
                    userAnswer = textInput.value;
                }
                
                // Check for textarea
                const textArea = box.querySelector('textarea');
                if (textArea) {
                    userAnswer = textArea.value;
                }
                
                // Check for radio input
                const checkedRadio = box.querySelector('.exercise-radio-input:checked');
                if (checkedRadio) {
                    // Get the label text for the checked radio
                    userAnswer = checkedRadio.parentElement.textContent.replace(checkedRadio.value, '').trim();
                } else {
                    // check if there are radios but none checked
                     if (box.querySelector('.exercise-radio-input')) {
                         userAnswer = "(No answer selected)";
                     }
                }
                
                exercises.push({
                    id: index + 1,
                    question_context: questionText,
                    user_answer: userAnswer
                });
            });

            if (exercises.length === 0) {
                 alert("No exercises found to submit.");
                 submitBtn.disabled = false;
                 submitBtn.textContent = originalText;
                 return;
            }

            try {
                // Parse URL to get course and module IDs
                // /learn/course{course_id}/module{module_number}
                const urlParts = window.location.pathname.split('/');
                // Assuming format /learn/course1/module1
                // We'll pass the whole path and let backend parse or pass IDs if we can extract them nicely.
                // Let's rely on the URL sending mechanism in the payload.
                
                const response = await fetch('/api/submit_module_answers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: window.location.pathname, 
                        exercises: exercises
                    })
                });
                
                const result = await response.json();
                
                const feedbackDiv = document.getElementById('module-feedback');
                feedbackDiv.classList.remove('hidden');
                
                if (result.success) {
                    feedbackDiv.innerHTML = `<h3>LLM Grading Feedback</h3>` + result.feedback_html;
                } else {
                    feedbackDiv.innerHTML = `<p class="error">Error: ${result.message}</p>`;
                }
                
            } catch (e) {
                console.error(e);
                alert("Error submitting answers");
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
});
