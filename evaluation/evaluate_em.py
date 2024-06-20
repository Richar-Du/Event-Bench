import json
import argparse
import os
import tqdm
def parse_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True, help="path to configuration file.")
    return parser.parse_args()

def check_ans(pred, gt):
    flag = False
    
    pred_list = pred.lower().split(' ')
    pred_option, pred_content = pred_list[0], ' '.join(pred_list[1:])
    gt_list = gt.lower().split(' ')
    gt_option, gt_content = gt_list[0], ' '.join(gt_list[1:])
    if gt_content[-1] == '.':
        gt_content = gt_content[:-1]
    
    if pred_option.replace('.', '') in gt_option:
        flag = True
    elif gt_option in pred_option:
        flag = True
        
    return flag

if __name__ == "__main__":
    args = parse_args()
    result = [json.loads(line) for line in open(args.input_file, 'r').readlines()]
    acc_dict = dict()

    for data in tqdm.tqdm(result):
        eval_result = 1
        for i in range(len(data['pred'])):
            pred = data['pred'][i]
            gt = data['gt'][i]
            eval_result *= check_ans(pred, gt)
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