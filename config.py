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