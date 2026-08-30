import re
from typing import Dict, List, Any

class LegalTacticalNLPExtractor:
    def __init__(self):
        self.statute_patterns = {
            'ipc_379': r'(?i)\b(?:section|sec\.?|u/s)?\s*379\s*(?:ipc)?\b',
            'ipc_420': r'(?i)\b(?:section|sec\.?|u/s)?\s*420\s*(?:ipc)?\b',
            'ipc_468_471': r'(?i)\b(?:section|sec\.?|u/s)?\s*(?:468|471|468/471)\s*(?:ipc)?\b',
            'ipc_120b': r'(?i)\b(?:section|sec\.?|u/s)?\s*120[\s-]?b\s*(?:ipc)?\b',
            'it_act_66d': r'(?i)\b(?:section|sec\.?|u/s)?\s*66[\s-]?d\s*(?:it act)?\b',
            'it_act_66c': r'(?i)\b(?:section|sec\.?|u/s)?\s*66[\s-]?c\s*(?:it act)?\b',
        }
        self.entity_patterns = {
            'phone_numbers': r'(?:\+91[\-\s]?)?[6789]\d{9}',
            'imei_numbers': r'\b\d{15}\b',
            'bank_accounts': r'\b[0-9]{9,18}\b',
            'ifsc_codes': r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        }
        self.custody_pattern = r'(?i)(?:custody|detention|jail)\s*(?:of|for)?\s*(\d+)\s*(?:days|months)'
        self.chargesheet_pattern = r'(?i)\b(?:charge[\s-]?sheet|final report)\s*(?:has been filed|submitted|filed)\b'
        self.account_frozen_pattern = r'(?i)\b(?:account|amount|funds?)\s*(?:has been |was )?(?:frozen|debit freeze)\b'

    def process_document(self, text: str) -> Dict[str, Any]:
        statutory_features = {
            k: (1 if re.search(pat, text) else 0)
            for k, pat in self.statute_patterns.items()
        }
        graph_entities = {
            k: list(set(re.findall(pat, text)))
            for k, pat in self.entity_patterns.items()
        }
        
        custody_days = 0
        c_match = re.search(self.custody_pattern, text)
        if c_match:
            val = int(c_match.group(1))
            if 'month' in c_match.group(0).lower():
                val *= 30
            custody_days = val

        judicial_milestones = {
            'charge_sheet_filed': 1 if re.search(self.chargesheet_pattern, text) else 0,
            'account_frozen_indicator': 1 if re.search(self.account_frozen_pattern, text) else 0,
            'custody_duration_days': custody_days
        }

        return {
            "statutory_features": statutory_features,
            "graph_entities": graph_entities,
            "judicial_milestones": judicial_milestones
        }