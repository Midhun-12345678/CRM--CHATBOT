# -*- coding: utf-8 -*-
"""CRM- PROMPT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1wMbuGteLkNS005PAjP0bB-wiyzarpOr4
"""

import pandas as pd
from google.colab import drive
drive.mount('/content/drive')

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import pandas as pd
import torch
import smtplib
from email.mime.text import MIMEText

df = pd.read_csv('/content/Mall_Customers (1).csv')
df.rename(columns={'Annual Income (k$)': 'income', 'Spending Score (1-100)': 'spending'}, inplace=True)
df.columns = df.columns.str.strip()

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

def parse_filter_condition(query):
    query = query.lower()
    age_condition = None

    if "aged between" in query:
        try:
            age_range = query.split("aged between")[-1].strip().split("and")
            min_age, max_age = int(age_range[0].strip()), int(age_range[1].strip())
            age_condition = f"Age >= {min_age} and Age <= {max_age}"
        except (IndexError, ValueError):
            return None
    elif "age above" in query:
        try:
            min_age = int(query.split("age above")[-1].strip())
            age_condition = f"Age > {min_age}"
        except ValueError:
            return None
    elif "age below" in query:
        try:
            max_age = int(query.split("age below")[-1].strip())
            age_condition = f"Age < {max_age}"
        except ValueError:
            return None

    return age_condition

def parse_conditions_from_prompt(prompt):
    age_min, age_max, spending_threshold = 20, 30, 50

    if "age" in prompt and "between" in prompt:
        try:
            age_range = prompt.split("aged between")[-1].split("and")
            age_min, age_max = int(age_range[0].strip()), int(age_range[1].strip())
        except (IndexError, ValueError):
            pass
    elif "age above" in prompt:
        try:
            age_min = int(prompt.split("age above")[-1].strip())
            age_max = None
        except ValueError:
            pass
    elif "age below" in prompt:
        try:
            age_max = int(prompt.split("age below")[-1].strip())
            age_min = None
        except ValueError:
            pass

    if "spending above" in prompt:
        try:
            spending_threshold = int(prompt.split("spending above")[-1].strip())
        except ValueError:
            pass

    return age_min, age_max, spending_threshold

def create_campaign_plan(prompt):
    age_min, age_max, spending_threshold = parse_conditions_from_prompt(prompt)

    if age_min is not None and age_max is not None:
        target_audience = df[(df['Age'] >= age_min) & (df['Age'] <= age_max) & (df['spending'] > spending_threshold)]
    elif age_min is not None:
        target_audience = df[(df['Age'] > age_min) & (df['spending'] > spending_threshold)]
    elif age_max is not None:
        target_audience = df[(df['Age'] < age_max) & (df['spending'] > spending_threshold)]
    else:
        target_audience = df[df['spending'] > spending_threshold]

    campaign_details = [
        f"Target Audience: {len(target_audience)} customers with specified conditions.",
        f"Age Range: {'All ages' if age_min is None and age_max is None else f'{age_min} - {age_max}'}",
        f"Spending Score Above: {spending_threshold}",
        "Offer: Exclusive 15% discount on purchases over $200.",
        "Message: 'Enjoy exclusive savings just for you!'",
        "Channels: Email and SMS.",
        "Duration: Next 2 weekends.",
        "Tracking: Monitor engagement and sales growth."
    ]
    return "\n".join(campaign_details)

def create_campaign(spending_threshold=80):
    high_spenders = df[df['spending'] > spending_threshold]
    steps = [
        "1. Identify high spenders based on the spending score.",
        f"2. Target {len(high_spenders)} customers with a spending score above {spending_threshold}.",
        "3. Prepare marketing materials tailored to this group.",
        "4. Schedule the campaign and monitor its effectiveness."
    ]
    return "Campaign Creation Steps:\n" + "\n".join(steps)


def generate_report(column_name, filter_condition=None):
    if column_name == "gender":
        gender_counts = df['Gender'].value_counts()
        return f"Gender distribution:\n{gender_counts.to_string()}"
    else:
        data = df.query(filter_condition)[column_name] if filter_condition else df[column_name]
        return data.describe()

def send_email(recipient, subject, body):
    smtp_server = "smtp.your-email-provider.com"
    smtp_port = 587
    sender_email = "your_email@example.com"
    password = "your_password"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient, msg.as_string())
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {e}"

def answer_specific_questions(query):
    query = query.lower()

    if "income of customer" in query:
        try:
            customer_id = int(query.split("customer")[-1].strip()) - 1
            return df.loc[customer_id, 'income'] if 0 <= customer_id < len(df) else "Customer not found."
        except (IndexError, ValueError):
            return "Please specify a valid customer ID."

    elif "spending of customer" in query:
        try:
            customer_id = int(query.split("customer")[-1].strip()) - 1
            return df.loc[customer_id, 'spending'] if 0 <= customer_id < len(df) else "Customer not found."
        except (IndexError, ValueError):
            return "Please specify a valid customer ID."

    elif "highest age" in query:
        return f"The highest age customer is {df['Age'].max()} years old."
    elif "highest spending" in query:
        return f"The highest spending score is {df['spending'].max()}."
    elif "gender with highest average income" in query:
        gender_income = df.groupby('Gender')['income'].mean().idxmax()
        return f"The gender with the highest average annual income is {gender_income}."

    return "I can't answer that question. Please try asking something else."

def chatbot(query):
    query = query.lower()

    if "create campaign" in query or "marketing campaign" in query:
        spending_threshold = 70
        if "above" in query:
            try:
                spending_threshold = int(query.split("above")[-1].strip())
            except ValueError:
                return "Please provide a valid number for the spending threshold."
        return create_campaign_plan(query)

    elif "report" in query:
        filter_condition = parse_filter_condition(query)
        if "income" in query:
            return generate_report("income", filter_condition)
        elif "spending" in query:
            return generate_report("spending", filter_condition)
        elif "gender" in query:
            return generate_report("gender")
        else:
            return "Specify a report type: income, spending, or gender."

    elif "send email" in query:
        recipient = "recipient@example.com"
        subject = "CRM Update"
        body = "This is a CRM update regarding your customer data."
        return send_email(recipient, subject, body)

    else:
        specific_answer = answer_specific_questions(query)
        if specific_answer != "I can't answer that question. Please try asking something else.":
            return specific_answer

        inputs = tokenizer.encode(query + tokenizer.eos_token, return_tensors="pt")
        reply_ids = model.generate(inputs, max_length=1000, pad_token_id=tokenizer.eos_token_id)
        return tokenizer.decode(reply_ids[:, inputs.shape[-1]:][0], skip_special_tokens=True)

print("Welcome to the CRM chatbot! Ask me anything about customer data.")
while True:
    user_query = input("User: ")
    response = chatbot(user_query)
    print(f"Bot: {response}")

