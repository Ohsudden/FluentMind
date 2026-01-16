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
                const questionText = box.innerText; 
                
                let userAnswer = "";
                
                const textInput = box.querySelector('.exercise-input');
                if (textInput) {
                    userAnswer = textInput.value;
                }
                
                const textArea = box.querySelector('textarea');
                if (textArea) {
                    userAnswer = textArea.value;
                }
                
                const checkedRadio = box.querySelector('.exercise-radio-input:checked');
                if (checkedRadio) {
                    userAnswer = checkedRadio.parentElement.textContent.replace(checkedRadio.value, '').trim();
                } else {
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

                const urlParts = window.location.pathname.split('/');

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
