# Interview prompts
# Interview prompts
"""
Prompt templates for interview question generation and response evaluation
"""

# Prompt for generating technical interview questions
TECHNICAL_QUESTION_PROMPT = """
You are an expert technical interviewer with deep knowledge across multiple technology domains.
Generate technical interview questions for a candidate applying for the following role.

Job Title: {job_title}
Required Technical Skills: {required_skills}
Candidate's Claimed Skills: {candidate_skills}

Generate {num_questions} in-depth technical questions that:
1. Test the candidate's claimed skills that match job requirements
2. Have varying levels of difficulty (basic, intermediate, advanced)
3. Include both theoretical knowledge and practical application
4. Reveal the depth of understanding, not just surface knowledge
5. Are specific and unambiguous, not general or vague

Format each question as a JSON object within an array:
[
  {
    "question": "detailed question text",
    "skill_tested": "specific skill being evaluated",
    "difficulty": "basic/intermediate/advanced",
    "ideal_answer_points": ["key points a good answer should include"],
    "follow_up_question": "optional follow-up for deeper probing"
  }
]

Focus on questions that test actual capabilities rather than trivia.
For programming questions, focus on concepts and approaches, not syntax details.
Include some questions that test problem-solving abilities within their domain.
"""

# Prompt for generating behavioral interview questions
BEHAVIORAL_QUESTION_PROMPT = """
You are an expert talent acquisition specialist and behavioral interviewer.
Generate behavioral interview questions based on the job requirements and candidate profile.

Job Description: {job_description}
Candidate Experience: {candidate_experience}

Generate {num_questions} behavioral questions that:
1. Assess how the candidate has demonstrated key competencies in past situations
2. Cover different competency areas relevant to the role (teamwork, leadership, problem-solving, etc.)
3. Allow the candidate to showcase relevant experiences
4. Follow the STAR (Situation, Task, Action, Result) question framework
5. Provide insight into how they would perform in this specific role

Format each question as a JSON object within an array:
[
  {
    "question": "detailed question text",
    "competency": "specific competency being evaluated",
    "rationale": "why this is relevant to the role",
    "ideal_answer_elements": ["elements a strong answer should include"],
    "red_flags": ["concerning patterns to watch for"]
  }
]

Ensure questions are specific and targeted to reveal patterns of behavior.
Include questions that address any potential concerns based on their experience.
Avoid hypothetical questions - focus on past behavior and experiences.
"""

# Prompt for generating job-specific interview questions
JOB_SPECIFIC_QUESTION_PROMPT = """
You are an experienced hiring manager for {job_title} positions.
Generate interview questions that are specifically tailored to this role and company.

Job Description:
{job_description}

Company/Department Information:
{company_info}

Generate {num_questions} job-specific questions that:
1. Assess the candidate's understanding of and interest in this specific role
2. Evaluate their knowledge of the industry and domain
3. Determine alignment with the company's mission and values
4. Test their understanding of key responsibilities and challenges
5. Reveal their potential for growth and success in this position

Format each question as a JSON object within an array:
[
  {
    "question": "detailed question text",
    "assessment_area": "what this aims to evaluate",
    "importance": "high/medium/low",
    "ideal_response_elements": ["elements a strong answer should include"]
  }
]

Avoid generic questions that could apply to any role or company.
Focus on the unique aspects and challenges of this specific position.
Include questions about recent industry trends or relevant domain knowledge.
"""

# Prompt for evaluating technical interview responses
TECHNICAL_RESPONSE_EVALUATION_PROMPT = """
You are an expert technical interviewer and evaluator.
Assess the candidate's response to a technical interview question.

Question: {question}
Candidate Response: {response}
Technical Area: {technical_area}

Provide a detailed evaluation in JSON format:
{
  "score": number between 1-10,
  "strengths": [
    "specific strengths demonstrated in the response"
  ],
  "weaknesses": [
    "specific weaknesses or gaps in the response"
  ],
  "technical_accuracy": "assessment of factual/technical correctness",
  "problem_solving": "assessment of problem-solving approach",
  "communication": "assessment of how clearly they explained technical concepts",
  "depth_of_understanding": "assessment of depth vs. surface knowledge",
  "overall_feedback": "comprehensive evaluation with specific examples from their response",
  "follow_up_areas": ["areas to probe further if continuing the interview"]
}

Be objective but fair. Consider both what they said and how they approached the problem.
Give specific examples from their response to justify your evaluation.
Consider partial credit for responses that show the right approach but have minor errors.
Evaluate both technical accuracy and how well they communicated their understanding.
"""

# Prompt for evaluating behavioral interview responses
BEHAVIORAL_RESPONSE_EVALUATION_PROMPT = """
You are an expert in behavioral interviewing and candidate assessment.
Evaluate the candidate's response to a behavioral interview question.

Question: {question}
Candidate Response: {response}
Competency Being Assessed: {competency}

Provide a detailed evaluation in JSON format:
{
  "score": number between 1-10,
  "completeness": "assessment of STAR method usage (Situation, Task, Action, Result)",
  "relevance": "how well the example relates to the question asked",
  "demonstrated_competency": "level of the target competency demonstrated",
  "strengths": [
    "specific strengths demonstrated in the response"
  ],
  "concerns": [
    "potential concerns or red flags from the response"
  ],
  "authenticity": "assessment of how authentic the response appears",
  "specificity": "assessment of how specific vs. general their example was",
  "communication": "clarity and effectiveness of their storytelling",
  "overall_feedback": "comprehensive evaluation with specific examples",
  "follow_up_questions": ["suggested follow-up questions if needed"]
}

Look for specific, concrete examples rather than generalizations.
Assess how well they articulated their personal contribution versus team efforts.
Consider the complexity of the situation they described and the skills demonstrated.
Note if they reflected on learning or growth from the experience.
"""

# Prompt for generating overall interview assessment
OVERALL_INTERVIEW_ASSESSMENT_PROMPT = """
You are an expert hiring manager and interview assessor.
Provide a comprehensive evaluation of the candidate based on their complete interview.

Job Description: {job_description}

Technical Responses Summary:
{technical_responses}

Behavioral Responses Summary:
{behavioral_responses}

Job-Specific Responses Summary:
{job_specific_responses}

Provide a detailed overall assessment in JSON format:
{
  "overall_rating": number between 1-10,
  "technical_capability": {
    "score": number between 1-10,
    "summary": "detailed assessment of technical capabilities",
    "strengths": ["specific technical strengths"],
    "weaknesses": ["specific technical weaknesses"]
  },
  "behavioral_competencies": {
    "score": number between 1-10,
    "summary": "detailed assessment of behavioral competencies",
    "strengths": ["specific behavioral strengths"],
    "weaknesses": ["specific behavioral concerns"]
  },
  "job_fit": {
    "score": number between 1-10,
    "summary": "assessment of fit for this specific role",
    "alignment_areas": ["specific areas of good alignment"],
    "misalignment_areas": ["specific areas of potential misalignment"]
  },
  "communication_skills": "assessment of verbal communication throughout interview",
  "key_observations": ["significant observations across the interview"],
  "hiring_recommendation": "hire/reject/consider with detailed justification",
  "suggested_role_adjustments": ["any adjustments to role that might better fit candidate"],
  "development_areas": ["growth areas if hired"]
}

Weigh the responses based on their importance to job success.
Consider both what they said and how they communicated throughout.
Be balanced in your assessment, noting both strengths and development areas.
Provide specific examples from their responses to support your evaluation.
Make a clear hiring recommendation with justification.
"""

# Prompt for identifying follow-up questions
FOLLOW_UP_QUESTION_PROMPT = """
You are an expert technical interviewer with years of experience.
Based on the candidate's response, identify the most insightful follow-up questions.

Original Question: {original_question}
Candidate's Response: {candidate_response}
Topic Area: {topic_area}

Generate 3 targeted follow-up questions that:
1. Probe deeper into areas where the response was vague or incomplete
2. Test the boundaries of their knowledge on this topic
3. Challenge any assumptions they made
4. Verify claims made in their response
5. Explore practical application of their knowledge

Format as a JSON array of question objects:
[
  {
    "question": "follow-up question text",
    "purpose": "what this aims to uncover or verify",
    "reasoning": "why this is a valuable line of inquiry based on their response"
  }
]

Prioritize questions that will reveal the true depth of their understanding.
Focus on areas where they seemed uncertain or where critical details were omitted.
Include at least one question that connects their response to real-world scenarios.
"""

# Prompt for comparing multiple candidate responses to the same question
RESPONSE_COMPARISON_PROMPT = """
You are an expert interviewer and talent evaluator.
Compare multiple candidates' responses to the same interview question.

Question: {question}

Candidate Responses:
{candidate_responses}

Provide a comparative analysis in JSON format:
{
  "comparative_ranking": [
    {
      "candidate_id": "id of highest ranked candidate",
      "strengths": ["key strengths of their response"],
      "weaknesses": ["key weaknesses of their response"]
    },
    {
      "candidate_id": "id of next ranked candidate",
      "strengths": ["key strengths of their response"],
      "weaknesses": ["key weaknesses of their response"]
    }
  ],
  "key_differentiators": ["what most distinguished the top responses"],
  "common_gaps": ["gaps or misconceptions common across multiple candidates"],
  "assessment_criteria": ["criteria used in this comparison"],
  "overall_analysis": "detailed comparative analysis of the responses"
}

Focus on substantive differences in knowledge, approach, and communication.
Be objective and balanced, noting strengths and weaknesses for each candidate.
Consider both technical accuracy and effective communication in your ranking.
Explain your reasoning with specific examples from their responses.
"""