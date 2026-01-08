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


english_test_check_propmt = """
You are a student who passes the placement test of English, solve it by writing in a way, Number - The letter of the answer.



Complete the sentences with the correct answers.

1 My sister _______ very tired today.

A be B am C is D are

2 His _______ is a famous actress.

A aunt B uncle C grandfather D son

3 I’d like to be a _______ and work in a hospital.

A lawyer B nurse C writer D pilot

4 We _______ like rap music.

A doesn’t B isn’t C aren’t D don’t

5 There _______ a lot of water on the floor. What

happened?

A are B is C be D am

6 He _______ TV at the moment.

A watches B is watching C watched

D has watching

7 Helen is very _______. She doesn’t go out a lot.

A bored B confident C angry D shy

8 Did you _______ to the beach yesterday?

A went B were C go D goed

9 Have you got _______ orange juice? I’m thirsty.

A some B a C any D the

10 Let’s go into _______ garden. It’s sunny outside.

A a B any C – D the

11 He’s _______ for the next train.

A looking B waiting C listening D paying

12 Mark _______ his car last week.

A cleaned B did clean C has cleaned

D is cleaning

13 I bought some lovely red _______ today.

A cabbages B cucumbers C bananas

D apples

14 Which bus _______ for when I saw you this

morning?

A did you wait B had you waited

C were you waiting D have you waited

15 Where _______ you like to go tonight?

A do B would C are D can

16 That’s the _______ film I’ve ever seen!

A worse B worst C baddest D most bad

17 My dad _______ his car yet.

A hasn’t sold B didn’t sell C doesn’t sell

D wasn’t sold

18 I’ve been a doctor _______ fifteen years.

A since B for C until D by

19 Look at the sky. It _______ rain.

A will B can C is going to D does

20 If I _______ this homework, the teacher will be

angry!

A am not finishing B won’t finish

C don’t finish D didn’t finished

21 This book is even _______ than the last one!

A most boring B boringer C more boring

D far boring

22 I’ll meet you _______ I finish work.

A if B when C as D so

23 We’re getting married _______ March.

A in B on C at D by

24 If you _______ steak for a long time, it goes hard.

A cook B are cooking C have cooked

D cooked

25 I _______ you outside the cinema, OK?

A ’ll see B am going to see C am seeing

D see

26 I _______ not be home this evening. Phone me

on my mobile.

A can B could C may D should

27 The criminal _______ outside the hotel last night.

A was caught B has been caught

C is caught D caught

28 He asked me if I _______ a lift home.

A wanted B want C was wanting

D had wanted

29 If I _______ older, I’d be able to vote in elections.

A had B am C were D have

30 You _______ go to the supermarket this

afternoon. I’ve already been.

A mustn’t B can’t C needn’t D won’t

31 Kathy drives _______ than her sister.

A more carefully B more careful C carefully

D most carefully

32 The _______ near our village is beautiful.

A country B woods C view D countryside

33 I’m _______ I can’t help you with that.

A apologise B afraid C regret D sad

34 It was really _______ this morning. I couldn’t see

anything on the roads.

A cloudy B sunny C icy D foggy

35 Can you look _______ my dog while I’m away?

A for B at C to D after

36 If I’d started the work earlier I _______ it by now.

A would finish B had finished C will finish

D would have finished

37 This time next year I _______ in Madrid.

A am working B will work C will be working

D work

38 I wish he _______ in front of our gate. It’s very

annoying.

A won’t park B wouldn’t park

C doesn’t park D can’t park

39 He said he’d seen her the _______ night.

A last B before C previous D earlier

40 I _______ agreed to go out. I haven’t got any

money!

A mustn’t have B shouldn’t have

C couldn’t have D wouldn’t have

41 It was good _______ about her recovery, wasn’t

it?

A information B words C news D reports

42 I _______ the report by 5.00 p.m. You can have it

then.

A have finished B will have finished

C finish D am finishing

43 Because of the snow the teachers _______ all

the students to go home early.

A said B made C told D demanded

44 Thanks for the meal! It was _______.

A delighted B delicious C disgusting

D distasteful

45 Look! Our head teacher _______ on TV right now!

A is being interviewed B is been interviewed

C is interviewing D is interviewed

46 It’s _______ to drive a car over 115 km/h in the

UK.

A unlegal B illegal C dislegal D legaless

47 There’s a lot of rubbish in the garden I need to

get _______ of.

A lost B rid C cleared D taken

48 I’m afraid it’s time we _______.

A leave B must leave C are leaving D left

49 He wondered what _______.

A is the time? B the time was

C was the time D is the time?

50 They _______ our salaries by 5%.

A rose B made up C raised D lifted 
"""
phoenix_tracker = PhoenixTracking(app_name="EnglishTestApp")
response = phoenix_tracker.generate_with_single_input(prompt = english_test_check_propmt, model = "gemini-2.5-flash-preview-09-2025")

print(response)