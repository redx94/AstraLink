""
File: policy_links.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
LIcense: Refer to LICENSE file in the root directory of this repository.

Links to the Privacy Policy and Terms and Conditions:

PRIVACY_POLICY_URL = "https://github.com/redx94/AstraLink/blob/main/docs/privacy_policy.md"
TERMS_AND_CONDITIONS_URL = "https://github.com/redx94/AstraLink/blob/main/docs/terms_and_conditions.md"

def get_policy_links():
    "Returns the URL structures for policies."
    return {
        "privacy_policy": PRIVACY_POLICY_URL,
        "terms_and_conditions": TERMS_AND_CONDITIONS_URL
    }

if __name__ == "__main__":
    print("Links:", get_policy_links())