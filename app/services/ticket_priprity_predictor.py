PRIORITY_KEYWORDS = {
    "urgent": [
        "server down",
        "system down",
        "production down",
        "data breach",
        "security breach",
        "entire system unavailable",
        "critical outage"
    ],
    "high": [
        "payment failed",
        "cannot pay",
        "unable to access",
        "service unavailable",
        "major issue",
        "multiple users affected"
    ],
    "medium": [
        "login issue",
        "password reset",
        "not working",
        "slow performance",
        "update failed"
    ],
    "low": [
        "general inquiry",
        "feature request",
        "profile picture",
        "suggestion",
        "information request"
    ]
}

def predict_ticket_priority(subject:str , description:str) -> str:

    text = f"{subject} {description}".lower()


    for priority, keywords in PRIORITY_KEYWORDS.items():

        for priority, keywords in PRIORITY_KEYWORDS.items():

         if any(keyword in text for keyword in keywords):
            return priority
     
    
    return "medium"

def explain_ticket_priority(
      subject: str,
      description: str
)-> dict:

   text = f"{subject} {description}".lower()

   for priority, keywords in PRIORITY_KEYWORDS.items():

         matched_keyword = [
         keyword
         for keyword in keywords
         if keyword in text
        ]

         if matched_keyword:

             reason = (
                       f"{priority.capitalize()} priority was selected "
                       f"because matching keywords were detected."
                )

             return{
                 "priority": priority ,
                 "matched_keywords": matched_keyword,
                 "reason": reason
              }

