# config.py

SOURCE = 'file'

MAIL_LINKS_FILE_START_ROW = 44
MAIL_LINKS_FILE_NUM_RECORDS = 1

SYSTEM = "You are a summarization assistant."
USER = "Provide once sentence summary of the text. Start the sentence with a verb like describes, explains or similar. TEXT START:\n\n"

PROMPTS = [
    "Summarize this text in one sentence, capturing its main idea.",
    "Provide a concise summary of this text in no more than three sentences.",
    "Distill the key points of this text into a brief paragraph.",
    "In 1-3 sentences, summarize the essential message of this passage.",
    "Create a one-line overview that encapsulates the text's core theme.",
    "Summarize this content in a way that highlights the most important details, keeping it under 50 words.",
    "Provide a short, focused summary of this text, no longer than three lines.",
    "Offer a concise recap of the main ideas from this passage in one or two sentences.",
    "Write a brief paragraph summarizing the most significant aspects of this text.",
    "Condense this content into a few sentences that capture its essence clearly and succinctly."
]

TEMPERATURE = 0.8
MODELS = [
     # # LLAMA
            # # small models < 8GB
            # "llama3.2:3b-instruct-fp16",
            # "llama3.2-vision:11b-instruct-fp16",
            #
            # # medium models 8GB - 24GB
            # "llama3.1:8b-instruct-fp16",
            #
            # # large models 24GB -  48GB
            # "llama3.1:70b-instruct-q4_K_M",
            # "llama3.2-vision:11b-instruct-fp16",
            # "llama3.3:70b-instruct-q2_K",
            # "llama3.3:70b-instruct-q4_K_M",
            #
            # # PHI
            # # small models < 8GB
            # "phi3:3.8b",
            # "phi3:3.8b-mini-128k-instruct-q4_K_M",
            # "phi3:14b",
            #
            # # medium models 8GB - 24GB
            # "phi3:14b-medium-128k-instruct-q8_0",
            # "phi4:14b-q8_0",
            #
            # # large models 24GB -  48GB
            # "phi3:14b-medium-128k-instruct-fp16",
            # "phi4:14b-fp16",
            #
            # #QWEN
            # # large models 24GB -  48GB
            # "qwen2.5:32b-instruct-q8_0",
            # "qwen2.5-coder:32b-instruct-q8_0",
            # "qwen2.5:72b-instruct-q4_K_S", # this one too, runs on CPU on 2x3090
            #
            # # STARCODER
            # # large models 24GB -  48GB
            # "starcoder2:15b-fp16",
            #
            # # GEMMA
            # # small models < 8GB
            # "gemma2:9b",
            #
            # # medium models 8GB - 24GB
            # "gemma2:27b",

            # # OPENAI
            # # only runs once to save tokens, see code
            "gpt-4o-mini-2024-07-18",

            # # UNCENSORED
            # "huihui_ai/llama3.3-abliterated",
            # "huihui_ai/llama3.3-abliterated-ft",
            # "dabl/L3.3-MS-Nevoria-70b-Q4_K_M.gguf",
            # "technobyte/Llama-3.3-70B-Abliterated:IQ2_XS",
            # "vanilj/theia-21b-v1",
            # "dolphin-mixtral:8x22b-v2.9-q2_K",
            # "dolphin-mixtral:8x7b-v2.5-q6_K",
            # "jean-luc/big-tiger-gemma:27b-v1c-Q6_K", # spanks GPU, runs on both in parallel (interesting), last one that spanks it


            # LEGACY
            # "qwen:72b", # ends up running on CPU on 2x3090 ... :( too slow on our rig
            # "command-r-plus:104b-08-2024-q2_K", #this one is 39GB, runs but still stresses CPU (but GPU also used now)
            # "command-r:latest", # GPU heavy, runs on both at about 50% each, and long, certainly longer than measured times
            # "command-r:35b-v0.1-q4_1", # GPU heavy, runs on both at about 50% each, and long, certainly longer than measured times
            # "command-r-plus:104b-08-2024-q3_K_S" # Still doesn't fit at 46GB, that is runs on CPU and slow
            # "command-r-plus:104b", # 55GB,need to drop to q3_K_S
            # "llama3.2-vision:90b", # on CPU, no quantization that will run on 2x3090 in VRAM
            # "phi3:14b", # take instruct not the genral one
            # "phi3","phi3.5" # crap
            # "dolphin-mixtral:8x22b", # good but slow, high CPU doesn't fit into 2x3090, overflows to RAM
            # "dolphin-mixtral", # too verbose
            # "llama3.1:70b-instruct-fp16", # 143GB don't run this locally 48GB VRAM and 64GB RAM is not enough
            # "command-r:latest", # not amazing
            # "llama3.1", # needs to be instruct? verbal diarrhea
            # "llama3.1:70b", # ditto
]

DB_PATH = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.db'
MBX_PATH = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.mbx'
CSV_PATH = 'extracted_articles.csv'

prompts_dict = {
    "product_vision": [
        """Rate the relevance of the provided document to **documenting product vision** on a scale of 0 to 100, based on the following:

        - 0: The document has no product vision content.
        - 50: The document mentions product vision but lacks depth.
        - 100: The document provides highly detailed product vision information.

        Output **only** the score as a single integer. No explanations or extra text.

        Example output:
        75
        """,
        """From the provided text, evaluate how relevant it is for **product vision documentation**. Respond with a single number (0-100).

        Only output a number. No explanation.
        """,
        """You are an evaluator tasked with rating a document's relevance for **product vision documentation** on a scale of 0-100. 

        Consider:
        - Does it describe the product vision clearly?
        - Does it include details like goals, roadmap, target users, and strategic direction?

        Provide **only** a single number as your output. Do not explain.

        Example:
        42
        """,
        """Imagine you're reviewing a technical document for product vision relevance. Your task is to assign it a score from 0 to 100:

        - 0: No product vision content.
        - 100: Fully detailed product vision documentation.

        Your response should be just the number, nothing else.
        """,
        """Review the document below for how well it documents product vision. Return the relevance score as an integer between 0 and 100.

        **Output format:**
        `score = <integer>`

        Example:
        `score = 85`
        """,
        """Assess the provided document for its relevance to **product vision documentation**. 

        - 0: No product vision content.
        - 100: Fully detailed product vision documentation.

        Provide only a single number as your output. No extra text.
        """,
        """Evaluate how well the document captures **product vision**. Rate it from 0 to 100 based on clarity, depth, and strategic insight.

        Output only a single integer. No explanations or additional text.
        """
    ],
    "product_roadmap": [
        """Rate the relevance of the provided document to **documenting a product roadmap** on a scale of 0 to 100:

        - 0: No roadmap content.
        - 50: Mentions roadmap but lacks depth.
        - 100: Detailed roadmap with milestones and timelines.

        Output only the score as an integer.
        """,
        """Evaluate the document for its usefulness in capturing a **product roadmap**. Rate from 0 to 100. 

        Respond with only a number. No extra text.
        """,
        """Does the document clearly define the **product roadmap**? Consider clarity, milestones, timelines, and priorities.

        Rate from 0 to 100. Output only the score.
        """,
        """Assess how effectively the document presents a **product roadmap**. 

        - 0: No roadmap content.
        - 100: A fully structured and actionable roadmap.

        Respond only with a single integer.
        """,
        """How well does the document describe the **product roadmap**, including phases, milestones, and dependencies? 

        Provide only a number between 0 and 100.
        """,
        """On a scale of 0 to 100, rate the document's effectiveness in presenting a **product roadmap** with key strategic steps. 

        Return only the number.
        """,
        """Examine the document's relevance to **product roadmap documentation**. 

        - 0: No roadmap-related details.
        - 100: A well-defined roadmap with clear sequencing.

        Output only the score.
        """
    ],
    "architecture_vision": [
        """Rate how well the document conveys an **architecture vision** on a scale from 0 to 100:

        - 0: No architectural vision content.
        - 50: Mentions architecture but lacks structure.
        - 100: A comprehensive and strategic architecture vision.

        Provide only a single integer score.
        """,
        """Evaluate the document for its relevance to **architecture vision**. 

        Return a number from 0 to 100. No explanation.
        """,
        """Does the document define an **architecture vision** with clear objectives, guiding principles, and future direction?

        Rate from 0 to 100 and output only the score.
        """,
        """Review the document's **architecture vision**. 

        - 0: No vision articulated.
        - 100: A strong and well-defined architecture vision.

        Provide only a single integer.
        """,
        """How well does the document outline an **architecture vision**, including principles, components, and evolution?

        Respond with only a number from 0 to 100.
        """,
        """Assess the document’s clarity and completeness in defining an **architecture vision**. 

        Provide only a single number between 0 and 100.
        """,
        """Evaluate how structured and forward-looking the **architecture vision** is. 

        Output a single integer from 0 to 100.
        """
    ],
    "service_vision": [
        """Rate the provided document’s relevance to defining a **service vision** from 0 to 100:

        - 0: No service vision details.
        - 100: Clear, structured, and strategic service vision.

        Output only a single integer.
        """,
        """Assess the document for how well it defines a **service vision**. 

        Provide only a score from 0 to 100.
        """,
        """Does the document explain a compelling **service vision**, including scope, objectives, and value? 

        Respond with only a number between 0 and 100.
        """,
        """How effectively does the document define a **service vision** for future development and customer impact? 

        Provide a single number from 0 to 100.
        """,
        """Evaluate the **service vision** clarity and strategic alignment. 

        Return only a number from 0 to 100.
        """,
        """Assess whether the document clearly articulates a **service vision** that aligns with customer needs and business objectives.

        Respond with only a number from 0 to 100.
        """,
        """Rate how well the document presents a **service vision** in terms of strategy, execution, and long-term goals. 

        Provide only a number from 0 to 100.
        """
    ],
    "security_vision": [
        """Rate the document’s relevance in defining a **security vision** from 0 to 100:

        - 0: No security-related vision.
        - 100: A comprehensive and well-structured security vision.

        Output only an integer.
        """,
        """Evaluate how well the document presents a **security vision**, covering risks, strategy, and controls. 

        Return only a score from 0 to 100.
        """,
        """Does the document outline a structured **security vision**, including principles and risk management? 

        Provide only a number from 0 to 100.
        """,
        """Assess the clarity and depth of the **security vision** within the document. 

        Respond with only a number from 0 to 100.
        """,
        """How effectively does the document define a **security vision** that aligns with organizational goals? 

        Provide only a score from 0 to 100.
        """,
        """Examine the document’s ability to convey a long-term **security vision**. 

        Respond only with a number from 0 to 100.
        """,
        """Rate the comprehensiveness of the **security vision** in the document, from 0 to 100. 

        Output only a single integer.
        """
    ],
    "lean_test_strategy": [
        """Rate how well the document defines a **lean test strategy** from 0 to 100:

        - 0: No test strategy content.
        - 100: A well-defined, efficient lean test strategy.

        Output only a single integer.
        """,
        """Evaluate the document’s relevance for describing a **lean test strategy**. 

        Provide only a score from 0 to 100.
        """,
        """Does the document articulate an effective **lean test strategy**, balancing efficiency and coverage? 

        Respond with only a number from 0 to 100.
        """,
        """How effectively does the document define a **lean test strategy**, including key principles and risk-based approaches? 

        Provide a single number.
        """,
        """Assess the document’s clarity and depth in presenting a **lean test strategy**. 

        Return only a number from 0 to 100.
        """
    ]
}
