from dotenv import load_dotenv
import os

load_dotenv()
import weaviate

# with weaviate.connect_to_local() as client:
#     print([c for c in client.collections.list_all()])
#     coll = client.collections.get("CefrGrammarProfile")
#     res = coll.query.fetch_objects(limit=3)
#     for obj in res.objects:
#         print(obj.properties)


from phoenix_tracking import PhoenixTracking
import time

english_test_check_propmt = """
You are a student who passes the placement test of English, solve it by writing in a way, Number - The letter of the answer.



Complete the sentences with the correct answers.

Questions 1–19
1. Pete _____ a teacher. a) isn't b) not c) aren't d) am not 





2. Bill _____ two brothers. a) have b) has c) is d) are 





3. A: _____ Italian food? B: Yes, I do. a) Are you like b) Likes c) Do you like d) You're like 





4. A: Was Shakespeare a painter? B: No, he _____. a) weren't b) didn't c) isn't d) wasn't 





5. _____ up early yesterday morning? a) Got b) Did you c) You get d) Did you get 





6. Peter _____ to work yesterday. a) not go b) didn't go c) didn't d) wasn't 





7. Can you _____ French? a) speak b) to speak c) speaks d) spoke 





8. A: Good night. B: _____  a) That's great. Thank you. b) No, I don't know.  c) You too. Sleep well.  d) Hello. How are you? 





9. A: How do you spell 'friend'?  B: _____ a) It's Miguel. b) F-R-I-E-N-D. c) My surname is Jackson. d) Yes, he is. 





10. A: How much is the camera? B: _____ a) It's on page thirty. b) It's from Spain. c) It's about six months old. d) It's fifty pounds. 





11. A: Excuse me. How do I get to the bus station? B: _____ a) In Oxford Street. b) Yes, that's right. c) It's about ten minutes. d) Go out of the school and turn right. 





12. A: What time were you born? B: _____ a) My birthday's in August. b) On the third of March. c) At six o'clock in the morning. d) In 1999. 





13. A: _____ B: I have a headache, that's all. a) What's the matter? b) Can I have a coffee, please? c) Thanks for everything. d) Here's a present for you. 





14. A: What's your job? B: I'm _____ a) married b) a doctor c) from Italy d) David Johnson 





15. John isn't Alice's _____. They aren't married. a) husband b) wife c) father d) mother 





16. What do they speak in _____? a) Spanish b) Portuguese c) American d) Brazil 





17. Your car keys are in the _____. a) lamp b) armchair c) drawer d) sofa 





18. We _____ a painting for €500. a) were b) said c) bought d) heard 





19. Do you play _____? a) ice hockey b) the cinema c) holidays d) sailing 





Questions 20–25

Read the text below, then choose the best answer. 

David Smith is a doctor. He works in a hospital. His wife, Angela, is a bank manager. They have two children, Robert and Susan. Robert is eleven and Susan is nine. They're at school. Last Sunday, the family got up early. David made a big breakfast of eggs and sausages. Then they went to the park. David and Robert played football, and Angela and Susan played tennis. The weather was beautiful. They enjoyed it. In the afternoon, they went out to a restaurant for lunch. 

20. David and Angela are _____ a) brother and sister b) married c) doctors d) bank managers 





21. Angela is Susan's _____ a) sister b) father c) mother d) brother 





22. Robert isn't _____ a) a student b) a child c) a doctor d) Susan's brother 





23. David, Angela, Robert and Susan went to the park _____. a) at night b) in the evening c) in the afternoon d) in the morning 





24. David _____ breakfast. a) didn't enjoy b) bought c) cooked d) didn't have 





25. They had _____ a) a holiday b) a lot of housework c) a horrible day d) a good time 





Questions 26–44
26. They _____ in Hong Kong in 2010. a) isn't b) aren't c) wasn't d) weren't 





27. _____ swim when I was five years old. a) I can b) I could c) I d) I was 





28. I _____ to my brother right now. a) 'm talking b) talk c) talking d) talked 





29. _____ to stay home and watch TV. a) I'm going b) I going c) Going d) Am going 





30. Helena has never _____ to Australia. a) went b) go c) been d) goes 





31. We _____ invite Tomas to the party. a) haven't b) won't c) not d) aren't 





32. A: _____  B: Sure. Good idea. a) What does 'bilingual' mean?  b) Can I open a window? It's hot in here. c) I like your jumper.  d) Excuse me! Can you help me? 





33. A: There's an Internet café in Park Lane, next to the bank. B: _____ a) Is that near here? b) Just two minutes, that's all. c) Do you need some money? d) Go straight ahead. 





34. A: _____ B: No, it isn't. a) Can I speak to Emma, please? b) What's the address? c) Can I take a message? d) Is that Emma? 





35. A: _____  B: Yes, please. It's delicious. a) Could you pass the salt, please? b) How would you like your coffee? c) Would you like some more rice? d) Is there any more salad left? 





36. A: What about this jacket?  B: _____ a) Credit card's fine. b) No, it isn't the right blue. c) How do you want to pay? d) Can I help you? 





37. A: _____ B: Well, we could go swimming. a) How are you feeling today? b) What shall we do this afternoon?  c) OK. I'll get my swimming costume. d) It's too cold to go swimming. 





38. A: How do you find living in New York? B: _____ a) No, I missed it.  b) Thank you. I'm glad you like it. c) I'm enjoying it a lot. d) I'm very well, thanks. 





39. I don't like preparing food, but I like _____ in restaurants. a) cooking b) eating c) going d) using 





40. The plates are in the _____. a) cups b) fridge c) cooker d) cupboard 





41. Can you _____ this from German to English? a) speak b) make c) think d) translate 





42. She speaks _____ Spanish. a) fluent b) hard c) well d) very 





43. It's a lovely day. It's _____. Let's go to the beach. a) cool and cloudy b) cold and foggy c) sunny and warm d) wet and windy 





44. My father is a nurse. He works in a _____. a) cinema b) hospital c) factory d) shop 





Questions 45–50

Read the text below, then choose the best answer. 

My name's Rachel. I like summer best. We cook and eat in the garden, and we often go to the beach. I don't like sunbathing, but I love swimming. I was born in a village near the seaside, and my family went to the beach almost every day. I could swim when I was a baby. I loved it then, and I love it now. My brother loves surfing and he's really good at it. He's the best surfer in our school. He's won ten or fifteen competitions. I've tried it, but I've never learnt to surf. Maybe I'll try it again when I retire! 

45. Rachel talks about _____ a) her plans for the future b) her favourite season c) what she did last month d) her favourite food 





46. Rachel talks about her _____ a) leisure activities b) working life c) school days d) parents and grandparents 





47. Rachel _____ when she was a very little girl. a) learned to swim b) didn't like swimming c) lived in the city d) rarely went to the beach 





48. Rachel's brother _____ surfing. a) is learning b) has never been c) has done a lot of d) is going to try 





49. Rachel _____ surfing. a) has never been b) isn't good at c) has won awards for d) hates 




50. Rachel's brother is _____ surfer than his classmates. a) an older b) a safer c) a worse d) a better 





Questions 51–69
51. I'm thinking _____ to Japan next year. a) of going b) I go c) goes d) going 





52. One day, I hope _____ China. a) will visit b) visit c) visiting d) to visit 





53. If I _____ travelling, I'll send you lots of postcards. a) 'll go b) went c) go d) 'll 





54. In the future, cities on Mars _____. a) are being built b) can build c) will be built d) are building 





55. All of the sandwiches _____. a) were eaten b) are eating c) were eating d) have eaten 





56. There was no money in the office when I arrived at work. All of it _____ by burglars. a) has been stolen b) had been stealing c) had stolen d) had been stolen 





57. A: _____ B: £8 for an adult, £4.50 for children under 12. a) How much is it to get in? b) I gave you a £10 note, not a £5 note. c) How much is a litre of petrol? d) It's cheaper if you buy a family ticket. 





58. A: _____  B: Cheer up! You've got me. I'm always here for you. a) I passed my exam. b) I'm getting married next week. c) I'm going on holiday to Australia tomorrow. d) I don't think I have many friends. 





59. A: What are your symptoms? B: _____ a) I've got a temperature and I feel awful. b) Just take it easy for a while. c) I've got food poisoning. d) Drink plenty of liquids. 





60. A: Hello? Hello? B: _____  a) I'm not sure. Can I get back to you later? b) Sorry, we were cut off.  c) OK. Speak to you soon. d) Oh, and can you give me Dean's number? 





61. A: Mike and Jo are such nice people. B: _____  a) I know. There were so many problems. b) Yes, I don't know how they live in it.  c) You're right. We had so much fun with them.  d) That's true. I don't know where it's all gone. 





62. A: I'll give you a lift into town if you like. B: _____ a) I'm sorry, it's not working today. b) I've got enough already thanks.  c) Go ahead. It's very hot in here. d) That would be great. 





63. I didn't have much time, so I did my homework _____. a) quickly b) lazily c) peacefully d) tragically 





64. I haven't got any _____. a) envelopes b) doughnuts c) stamps d) deodorant 





65. We were _____ during the film. It wasn't interesting at all. a) shocked b) bored c) annoyed d) depressed 





66. I'm _____ a lot of training for my new job. a) spending b) studying c) doing d) working 





67. Henry wants to study at Oxford University, but he also wants to study at Cambridge University. He can't _____ up his mind. a) get b) go c) take d) make 





68. I _____ my job because the hours were too long. a) gave up b) took off c) put away d) went back 





69. My brother really _____ my father. a) picks up b) gets on c) takes after d) looks up 





Questions 70–75

Read the text below, then choose the best answer. 

Greg is 21 years old. He's been studying at Manchester University for the past three years, but he's going to finish his course next month. 'I'd like to get a job here in Manchester,' he says, 'but that may not be possible. My degree is in business, and I'd like to work in management. But there aren't a lot of jobs right now, and I haven't got any money. I'm feeling a bit nervous and depressed about finding a job, actually. It's on my mind a lot. I'm afraid I won't find one, and I'll be unemployed for a long time.' If Greg doesn't find a job in Manchester, he'll look for something in nearby Leeds or Sheffield. 'As soon as I finish my exams, I'll start applying,' he says. 'That's next month. Right now, I need to concentrate on my studies.' He adds, 'I don't think I'll be happy until I start working in Manchester.' 

70. Greg _____ a) would like to leave Manchester b) hopes to continue studying for another year c) hasn't finished his course yet d) wasn't studying last year 





71. Greg _____ business. a) would like to study b) is studying c) already has a job in d) isn't interested in 





72. Greg _____ finding a job. a) doesn't think a lot about b) thinks it won't be difficult c) says he feels confident about d) feels worried about 





73. Greg is going to apply for jobs in Leeds and Sheffield _____ in Manchester. a) after trying for a job b) as soon as he finds a job c) while he's applying for jobs d) before he looks for work 





74. At the moment, Greg's main focus is _____ a) his studies b) applying for jobs c) searching for a flat d) preparing to move 





75. Greg won't be happy if he doesn't _____ a) fail his exams b) have his exams next month c) get work in Leeds or Sheffield d) find a job in Manchester 



Questions 76–93
76. The sign says No parking. We _____ to park here. a) shouldn't b) aren't allowed c) can't d) should 





77. A: How long have you _____ English? B: For about six years. a) studying b) been studying c) study d) to study 





78. If _____ told me about your problems, I'd have helped. a) you'll b) you're c) you've d) you'd 





79. We can text _____ after work and arrange a place to meet. a) each other b) each c) us d) another 





80. I saw Mrs Jones yesterday. She was surprised and asked me what _____. a) are you doing b) am I doing c) I was doing d) if I'm doing 





81. I wish _____ before you speak. a) 'd think b) 'll think c) think d) 're thinking 





82. A: _____  B: Oh, dear. I'd love to, but this weekend I'm so busy. a) Are you doing anything next Saturday afternoon? b) I was wondering if we could meet next Saturday morning. c) What are you doing next Sunday evening? d) I'm afraid I've already got something to do on Sunday. 





83. A: I failed my driving test again. B: _____ a) Absolutely. b) That's too bad. c) Fair enough. d) That's amazing! 





84. A: I think you must have made a mistake. I'm pretty sure I gave you a £20 note. B: _____  a) Thanks. That's for you.  b) Yes, I'm afraid it is. But it doesn't include tax.  c) Sure. Tell me your account number.  d) Oh, did you? Er... sorry about that. 





85. A: What time will we arrive? B: _____ a) Presumably, the others will be late. b) Generally, on time. c) Hopefully, in the next hour. d) Obviously, we're late. 





86. A: _____  B: Oh, well. You live and learn. a) I trusted Adam and he stole my money. b) I've got ten exams in the next two weeks. c) I forgot her birthday, so I sent her a text. d) I wonder if their marriage will last. 





87. A: _____  B: In your dreams. Not if you were the last man on earth. a) Come on, you know you want to go out with me really.  b) I'm cleaned out! This new jacket cost the earth. c) We're throwing caution to the wind and emigrating to Australia. d) I'm really tired, so I'm going to stay home tonight. 





88. His attendance is _____. Some weeks he comes every day, other weeks he misses several classes. a) irregular b) unsuitable c) untrue d) inaccurate 





89. I don't eat much fruit. I'm not that _____ on it. a) crazy b) keen c) fond d) excited 





90. A lot of people visited the art gallery to see the painter's _____. a) service b) masterpiece c) architecture d) headline 





91. Two men _____ jail last night. a) broke out of b) sorted out c) took up d) broke up with 





92. I felt bad because my brother and I _____. a) admitted b) accused c) quarrelled d) criticized 





93. The sailors didn't see _____ for two months as they crossed the Atlantic. a) world b) earth c) ground d) land 





Questions 94–100

Read the text below, then choose the best answer. 

Seamus Carver had lived next door to Andrew Smith for about two years before they met. 'Seamus used to go to work early in the morning and come home in the afternoon, and I used to work nights at the factory,' said Andrew. 'We were never home at the same time. He worked on Saturdays and Sundays, and had Tuesdays and Wednesdays off. We never had a good look at each other. But when both men retired in the same year, their schedules changed. 'We'd both been out to the cinema one night, and we came home at the same time and met in front of our houses.'

'Right away, Seamus asked me if I'd gone to school at Oak Park Primary School in York. I said that I had, and then I understood. He and I had known each other for a year or two when we were young kids, like maybe six. And amazingly, we still remembered each other!' Both Seamus and Andrew said their families had moved away from York when they were young. What they hadn't realised was that both families had moved to Bristol, and both men had been living there ever since. 

94. Seamus and Andrew became next door neighbours _____ a) two years after they first met b) before they met c) after they met at work d) because they were friends 





95. While they were working, they _____ a) tried to meet b) sometimes met c) didn't meet d) didn't get along well 





96. When they met, they _____ the cinema. a) hadn't yet been to b) were in c) were leaving d) were coming home from 





97. Seamus asked, "_____ to Oak Park Primary School in York?" a) Have you ever been b) Did you go c) Were you going d) Had you gone 





98. Seamus and Andrew had been friends _____ a) after their families had moved to Bristol b) for the past two years c) their whole lives d) when they were very young 





99. Andrew and Seamus had known each other _____ a) when they were one or two years old b) for about six years, as kids c) when they were about six years old d) for the past six years 





100. Andrew said that _____ remembered each other. a) it would have been amazing if they had b) he wasn't shocked that they c) he was surprised that they d) he hadn't realised that they
"""

evaluate = """
You are an English tutor helping a student improve their writing.

Student task:
"Write a short paragraph (3–4 sentences) about your favorite hobby in the past tense."

Student response:
"I like play basketball when I was young. I am practice every day with my friends. 
We win many games and feel very happy."

Instructions:
- Read the student’s response carefully.
- Help the student improve their English.
- Do NOT rewrite the paragraph for the student.
- Point out any mistakes you notice.
- Explain the mistakes clearly and give helpful guidance.
- Encourage the student and keep a supportive tone.

"""

phoenix_tracker = PhoenixTracking(app_name="EnglishTestApp")
start_time = time.time()
response = phoenix_tracker.generate_with_single_input(prompt = evaluate, model = "gemini-2.5-flash-preview-09-2025")
end_time = time.time()
print(f"Time taken for gemini-2.5-flash-preview-09-2025: {end_time - start_time} seconds")
print(f"Response Gemini 2.5-flash-preview-09-2025: {response}")
start_time = time.time()
response = phoenix_tracker.generate_with_single_input(prompt = evaluate, model = "gemini-2.0-flash")
end_time = time.time()
print(f"Time taken for gemini-2.0-flash: {end_time - start_time} seconds")
print(f"Response Gemini 2.0-flash: {response}")
start_time = time.time()
response = phoenix_tracker.generate_with_single_input(prompt = evaluate, model = "gpt-5-mini", family="openai")
end_time = time.time()
print(f"Time taken for gpt-5-mini: {end_time - start_time} seconds")
print(f"Response GPT-5-mini: {response}")
start_time = time.time()
response = phoenix_tracker.generate_with_single_input(prompt = evaluate, model = "gpt-5.2", family="openai")
end_time = time.time()
print(f"Time taken for gpt-5.2: {end_time - start_time} seconds")
print(f"Response GPT-5.2: {response}")

