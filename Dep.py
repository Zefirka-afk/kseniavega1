pip install openai
from openai imort OpenAI
client = OpenAI(
    api_key="sk-aitunnel-29ONS5HJPvC4SIhUzX1lqbvwi6dSQ5jC", # Ключ из нашего сервиса
    base_url="https://api.aitunnel.ru/v1/",
)

chat_result = client.chat.completions.create(
    messages=[{"role": "user", "content": "Скажи интересный факт"}],
    model="deepseek-r1",
    max_tokens=50000, # Старайтесь указывать для более точного расчёта цены
)
print(chat_result.choices[0].message)
