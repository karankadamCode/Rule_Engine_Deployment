import csv
import json
import pandas as pd
from flask import Flask, render_template, request
import re
from flask import request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Loading JSON data from file
with open('firm.json', 'r') as file:
    data = json.load(file)


# Converting JSON to DataFrame/CSV
df_list = []
for state, rules in data['rules'].items():
    index = 1
    for rule in rules:
        condition = rule['condition']
        df_list.append({
            # 'rule_no': index,
            'action': rule['action'],
            'case_rating': condition['case_rating'],
            'case_state': condition['case_state'],
            'case_type': condition['case_type']
        })
        index += 1

df = pd.DataFrame(df_list)

df.to_csv('rules.csv', index=False)



# loading rules
def load_rules():
    rules = []
    try:
        with open('rules.csv', 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    row['case_rating'] = row['case_rating'].split()[-1]  # Extract only numeric part
                    match = re.search(r"Assign handling firm '(.*?)'(.*)", row['action'])
                    if match:
                        # If the action starts with "Assign handling firm", extract firm name and details
                        handling_firm = match.group(1)
                        details = match.group(2).strip()  # Trim any leading/trailing whitespace
                        row['action'] = f"'{handling_firm}'{details}"  # Reconstruct the action
                    rules.append(row)
                except Exception as e:
                    print(f"Error processing row: {row}. Error: {e}")
    except FileNotFoundError:
        print("File 'rules.csv' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return rules




# Function to convert CSV to JSON
def csv_to_json(csv_file):
    data = {}
    try:
        with open(csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    state = row['case_state']
                    if state not in data:
                        data[state] = []
                    condition = {
                        "case_type": row['case_type'],
                        "case_rating": row['case_rating'],
                        "case_state": row['case_state']
                    }
                    action = {
                        "action": row['action'],
                        "condition": condition
                    }
                    data[state].append(action)
                except Exception as e:
                    print(f"Error processing row: {row}. Error: {e}")
    except FileNotFoundError:
        print(f"File '{csv_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return {"rules": data}




#home route
@app.route('/')
def index2():
    try:
        rules = load_rules()
        states = sorted(set(rule['case_state'] for rule in rules))
        return render_template('index.html', states=states)
    except Exception as e:
        print(f"An error occurred while loading rules: {e}")
        # Handle the error accordingly, e.g., return an error response or render an error page
        return render_template('error.html', error_message='An error occurred while loading rules. Please try again later.'), 500



new_state_rules = []


#fetching rules
@app.route('/get_rules', methods=['POST'])
def get_rules():
    try:
        global new_state_rules  # Declare the global variable
        state = request.form['state']
        rules = load_rules()
        state_rules = [rule for rule in rules if rule['case_state'] == state]
        new_state_rules = [rule for rule in rules if rule['case_state'] != state]
        return {'rules': state_rules}
    except Exception as e:
        print(f"An error occurred while retrieving rules: {e}")
        # Handle the error accordingly, e.g., return an error response
        return jsonify({'error': 'An error occurred while retrieving rules. Please try again later.'}), 500





# Function to update rules in CSV file
def update_rules_csv(updated_rules):
    try:
        with open('rules.csv', 'w', newline='') as file:
            fieldnames = ['action', 'case_rating', 'case_state', 'case_type']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rules)
    except Exception as e:
        print(f"An error occurred while updating the rules CSV file: {e}")



# Function to append a new rule to the text file
def add_rule_to_txt(new_rule):
    try:
        # Append the new rule to the text file for storage
        with open('new_rules.txt', 'a') as file:
            file.write(json.dumps(new_rule) + '\n')
    except Exception as e:
        print(f"An error occurred while adding a new rule to the text file: {e}")



# Function to append a new rule to JSON data
def add_rule_to_json(new_rule):
    try:
        with open('firm.json', 'r+') as file:
            data = json.load(file)
            state = new_rule['case_state']
            if state not in data['rules']:
                data['rules'][state] = []
            data['rules'][state].append({
                "action": new_rule['action'],
                "condition": {
                    "case_type": new_rule['case_type'],
                    "case_rating": new_rule['case_rating'],
                    "case_state": state
                }
            })
            file.seek(0)  # Move to the beginning of the file
            json.dump(data, file, indent=4)  # Write the updated JSON data
            file.truncate()  # Truncate the remaining content if any
    except Exception as e:
        print(f"An error occurred while adding a new rule to the JSON file: {e}")
    
  

# validating case ratings
def validate_case_rating(case_rating):
    try:
        if isinstance(case_rating, str):
            # Check for leading zeros
            if case_rating.startswith('0'):
                return False
            
            # Check for multiple consecutive dashes
            if '--' in case_rating:
                return False
            
            if "-" in case_rating:
                parts = case_rating.split("-")
                if len(parts) != 2:
                    return False
                low, high = parts
                if not low.isdigit() or not high.isdigit():
                    return False
                low = int(low)
                high = int(high)
                if low < 1 or high > 5 or low > high:
                    return False
            else:
                if not case_rating.isdigit():
                    return False
                rating = int(case_rating)
                if rating < 1 or rating > 5:
                    return False
        else:
            return False
        return True
    except Exception as e:
        print(f"An error occurred while validating the case rating: {e}")
        return False



#adding rules
@app.route('/add_rule', methods=['POST'])
def add_rule():
    try:
        new_rule = request.json['new_rule']
        
        # Validate the case rating
        if 'case_rating' in new_rule and not validate_case_rating(new_rule['case_rating']):
            return "Invalid case rating format. Case rating must be in the format 1-5 or a single number from 1 to 5."
        
        # Call function to add the rule to the text file
        add_rule_to_txt(new_rule)
        
        # Call function to add the rule to the JSON data
        add_rule_to_json(new_rule)

        # Append the new rule to the CSV file
        with open('rules.csv', 'a', newline='') as file:
            fieldnames = ['action', 'case_rating', 'case_state', 'case_type']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(new_rule)

        # Loading JSON data from file
        with open('firm.json', 'r') as file:
            data = json.load(file)

        # Converting JSON to DataFrame/CSV
        df_list = []
        for state, rules in data['rules'].items():
            index = 1
            for rule in rules:
                condition = rule['condition']
                df_list.append({
                    # 'rule_no': index,
                    'action': rule['action'],
                    'case_rating': condition['case_rating'],
                    'case_state': condition['case_state'],
                    'case_type': condition['case_type']
                })
                index += 1

        df = pd.DataFrame(df_list)

        df.to_csv('rules.csv', index=False)
        
        return "New rule added successfully!"
    except Exception as e:
        print(f"An error occurred while adding a new rule: {e}")
        # Handle the error accordingly, e.g., return an error response
        return jsonify({'error': 'An error occurred while adding a new rule. Please try again later.'}), 500




#removing rules
@app.route('/remove_rule', methods=['POST'])
def remove_rule():
    try:
        rule_to_remove = request.json['rule_to_remove']
        updated_rules = load_rules()
        updated_rules = [rule for rule in updated_rules if rule != rule_to_remove]
        update_rules_csv(updated_rules)
        return "Rule removed successfully!"
    except Exception as e:
        print(f"An error occurred while removing a rule: {e}")
        # Handle the error accordingly, e.g., return an error response
        return jsonify({'error': 'An error occurred while removing a rule. Please try again later.'}), 500




# Function to validate the case rating format
def validate_case_rating_format(case_rating):
    try:
        # Check if case_rating is a string
        if isinstance(case_rating, str):
            # Check for multiple consecutive dashes
            if '--' in case_rating:
                return False

            if "-" in case_rating:
                # Split the case_rating on a single dash
                parts = case_rating.split("-")
                if len(parts) != 2:
                    return False

                lower, upper = parts
                if lower.isdigit() and upper.isdigit():
                    lower = int(lower)
                    upper = int(upper)
                    return 1 <= lower <= upper <= 5
                else:
                    return False
            else:
                if case_rating.isdigit():
                    rating = int(case_rating)
                    return 1 <= rating <= 5
                else:
                    return False
        return False
    except Exception as e:
        print(f"An error occurred while validating the case rating format: {e}")
        return False




#updating rules
def update_rules(updated_rules):
    try:
        # Validate all rules before updating the file
        for rule in updated_rules:
            case_rating = rule.get('case_rating')
            if not validate_case_rating_format(case_rating):
                return jsonify({'error': 'Invalid case rating format. Please provide a valid format (e.g., 1-4, 5).'}), 400
            # Ensure that 'action' field is in the desired format
            if not rule['action'].isdigit():  # Check if action is a number
                if not rule['action'].startswith("Assign handling firm"):
                    rule['action'] = "Assign handling firm " + rule['action']

        # If all rules are valid, proceed to update the file
        with open('rules.csv', 'w', newline='') as file:
            fieldnames = ['case_type', 'action', 'case_rating', 'case_state']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for rule in updated_rules:
                writer.writerow(rule)
    except Exception as e:
        print(f"An error occurred while updating the rules: {e}")
        # Handle the error accordingly, e.g., return an error response
        return jsonify({'error': 'An error occurred while updating the rules. Please try again later.'}), 500




# Endpoint to update rules
@app.route('/update_rules', methods=['POST'])
def update_rules_endpoint():
    try:
        updated_rules = request.json['updated_rules']

        # Combine the updated rules with the new state rules
        updated_rules.extend(new_state_rules)

        # Update rules in CSV file
        update_result = update_rules(updated_rules)
        if isinstance(update_result, tuple):  # If error occurred
            return update_result

        # Convert updated rules to JSON and save to file
        json_data = csv_to_json('rules.csv')
        with open('firm.json', 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        # Construct the success message
        success_message = "Rules updated successfully "

        # Find the index of the updated rule within its case state
        updated_rule_index = {}
        for rule in updated_rules:
            if rule in new_state_rules:
                continue  # Skip new state rules
            case_state = rule['case_state']
            if case_state not in updated_rule_index:
                updated_rule_index[case_state] = 1
            else:
                updated_rule_index[case_state] += 1

        # Update the success message for each case state
        for rule in updated_rules:
            case_state = rule['case_state']
            if case_state in updated_rule_index:
                index = updated_rule_index[case_state]
                success_message += f"for case state {case_state}."
                del updated_rule_index[case_state]

        # Print success message
        print(success_message)

        return success_message
    except Exception as e:
        print(f"An error occurred while updating rules: {e}")
        # Handle the error accordingly, e.g., return an error response
        return jsonify({'error': 'An error occurred while updating rules. Please try again later.'}), 500


# X-Frame-Options header
@app.after_request
def add_header(response):
    # Set the X-Frame-Options header to allow framing from localhost
    response.headers['X-Frame-Options'] = 'ALLOW-FROM http://localhost'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
