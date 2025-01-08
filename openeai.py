from openai import OpenAI

client = OpenAI(api_key ="Palmeiras tem mundial?", base_url= "http://localhost:11434/v1/")

responde = client.chat.completions.create(
    model ="llama3.1",
    messages=[
        {"role": "user","content":""}   
    ],
stream=False
)

print(responde.choices[0].message.content)





