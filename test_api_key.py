from google import genai
from decouple import config

GEMINI_API_KEY = config("GEMINI_API_KEY")

# client = genai.Client(api_key="YOUR_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

interaction = client.interactions.create(
    # model="gemini-3.8-flash",
    model = config("GEMINI_MODEL"),
    input="what is Python?"
)
print(interaction.output_text)