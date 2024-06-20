import openai
openai.api_base = ""
openai.api_key = ''
gpt_model = 'gpt-4-turbo-2024-04-09'
import time
import json
import tqdm
from multiprocessing import Pool
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--input_file", type=str)
parser.add_argument("--output_file", type=str)
args = parser.parse_args()

def parse_gpt_judge(content):
    if '1' in content:
        return 1
    else:
        return 0
    
system_prompt = '''
You are an intelligent chatbot designed for evaluating the correctness of generative outputs for question-answer pairs. Your task is to compare the predicted answer with the correct answer and determine if they match meaningfully. Here's how you can accomplish the task:
------
##INSTRUCTIONS:
- Focus on the meaningful match between the predicted answer and the correct answer.
- Consider synonyms or paraphrases as valid matches.
- Evaluate the correctness of the prediction compared to the answer.
'''

def judge(ele):
    template = '''Please evaluate the correctness of the following video-based question-answer pair:
Question: {}
Correct Answer: {}
Predicted Answer: {}
If the predicted answer expresses the same meaning as the correct answer, please output 1; otherwise, output 0.
DO NOT PROVIDE ANY OTHER OUTPUT TEXT OR EXPLANATION. Only provide 0 or 1.
'''
    gpt_judge = []
    eval_result = 1
    for i in range(len(ele['pred'])):
        text_options = "\n".join([f"({chr(ord('A')+j)}) {option}" for j, option in enumerate(ele['candidates'][i])])
        question = (
            f"{ele['question']}\n"
            f"Options:\n{text_options}"
        )
        prompt = template.format(question, ele['gt'][i], ele['pred'][i])
        max_retries = 20
        retry_delay = 5
        retries = 0
        output = None
        while output is None and retries < max_retries:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
                output = openai.ChatCompletion.create(
                    model=gpt_model,
                    max_tokens=10,
                    temperature=0,
                    messages=messages)
                if output is not None:
                    output = output['choices'][0]['message']['content']
                else:
                    retries += 1
                    print(f"Attempt {retries}: Failed to get response, retrying after {retry_delay} seconds...")
                    time.sleep(retry_delay)  
            except Exception as e:
                print(f"An error occurred: {e}")
                retries += 1
                print(f"Attempt {retries}: Exception encountered, retrying after {retry_delay} seconds...")
                time.sleep(retry_delay) 
        
        if output is None:
            print("Failed to get a valid response from the API after maximum retries.")
            gpt_judge.append("No response")
        else:
            gpt_judge.append(output)
        eval_result *= parse_gpt_judge(output)
        if not eval_result:
            break
    ele['gpt_judge'] = gpt_judge
    ele['eval_result'] = eval_result
    return ele

if __name__ == "__main__":
    output_file = open(args.output_file, 'a')
    gpt_input = [json.loads(line) for line in open(args.input_file, 'r').readlines()]
    result = []
    # uncomment for sequential evaluation
    # for ele in gpt_input:
    #     result.append(judge(ele))
    # uncomment for parallel evaluation
    with Pool(50) as p:
        result = list(tqdm.tqdm(p.imap(judge, gpt_input), total=len(gpt_input)))
    for ele in result:
        output_file.write(json.dumps(ele)+"\n")


    acc_dict = dict()

    for data in tqdm.tqdm(result):
        eval_result = data['eval_result']
        if data['task'] not in acc_dict:
            acc_dict[data['task']] = [eval_result]
        else:
            acc_dict[data['task']].append(eval_result)

    # Print table header
    header = f"{'Task':<30} {'Total':<10} {'Correct':<10} {'Accuracy':<10}"
    print(header)
    print("=" * len(header))

    # Print each task's results
    for task, accs in acc_dict.items():
        acc = sum(accs) / len(accs)
        print(f"{task:<30} {len(accs):<10} {sum(accs):<10} {acc*100:.2f}%")

    # Print overall accuracy
    overall_acc = sum(sum(accs) for accs in acc_dict.values()) / sum(len(accs) for accs in acc_dict.values()) * 100.0
    print("=" * len(header))
    print(f"{'Overall Accuracy':<30} {'':<10} {'':<10} {overall_acc:.2f}%")