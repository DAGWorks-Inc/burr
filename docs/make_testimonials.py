card_template = """
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"{user_quote}"</p>
                <h4>{user_name}</h4>
                <span>{user_title}, {user_company}</span>
            </div>
        </div>"""

testimonials = [
    {
        "user_name": "Ashish Ghosh",
        "user_title": "CTO",
        "user_company": "Peanut Robotics",
        "user_quote": "After evaluating several other obfuscating LLM frame-works, their elegant yet comprehensive state management "
        "solution proved to be the powerful answer to rolling out robots driven by AI decision making.",
        "image_link": "",
    },
    {
        "user_name": "Reddit User",
        "user_title": "LocalLlama",
        "user_company": "Subreddit",
        "user_quote": "Of course, you can use it [LangChain], but whether it's really production-ready and improves the time from 'code-to-prod' [...], "
        "we've been doing LLM apps for two years, and the answer is no [...] All these 'all-in-one' libs suffer from this [...].  "
        "Honestly, take a look at Burr. Thank me later.",
        "image_link": "",
    },
    {
        "user_name": "Ishita",
        "user_title": "Founder",
        "user_company": "Watto.ai",
        "user_quote": "Using Burr is a no-brainer if you want to build a modular AI application. It is so easy to build "
        "with and I especially love their UI which makes debugging, a piece of cake. And the always ready "
        "to help team, is the cherry on top.",
        "image_link": "",
    },
    {
        "user_name": "Matthew Rideout",
        "user_title": "Staff Software Engineer",
        "user_company": "Paxton AI",
        "user_quote": "I just came across Burr and I'm like WOW, this seems like you guys predicted this exact need when"
        " building this. No weird esoteric concepts just because it's AI.",
        "image_link": "",
    },
    {
        "user_name": "Rinat Gareev",
        "user_title": "Senior Solutions Architect",
        "user_company": "Provectus",
        "user_quote": "Burr's state management part is really helpful for creating state snapshots and build debugging, "
        "replaying and even building evaluation cases around that",
        "image_link": "",
    },
    {
        "user_name": "Hadi Nayebi",
        "user_title": "Co-founder",
        "user_company": "CognitiveGraphs",
        "user_quote": "I have been using Burr over the past few months, and compared to many agentic LLM platforms out "
        "there (e.g. LangChain, CrewAi, AutoGen, Agency Swarm, etc), Burr provides a more robust framework"
        " for designing complex behaviors.",
        "image_link": "",
    },
    {
        "user_name": "Aditya K.",
        "user_title": "DS Architect",
        "user_company": "TaskHuman",
        "user_quote": "Moving from LangChain to Burr was a game-changer! "
        "<br/>Time-Saving: It took me just a few hours to get started with Burr, compared to the days and weeks I spent trying to navigate LangChain. "
        "<br/>Cleaner Implementation: With Burr, I could finally have a cleaner, more sophisticated, and stable implementation. No more wrestling with complex codebases. "
        "<br/>Team Adoption: I pitched Burr to my teammates, and we pivoted our entire codebase to it. It's been a smooth ride ever since.",
        "image_link": "",
    },
]

# code to generate testimonials
for testimonial in testimonials:
    print(card_template.format(**testimonial))
