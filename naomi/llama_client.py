import json
import os
import re
import requests
import sqlite3
from datetime import datetime
from jinja2 import Template
from naomi import paths
from naomi import profile
from naomi import visualizations
from typing import List, Sequence


LLM_STOP_SEQUENCE = "<|eot_id|>"  # End of sentence token for Meta-Llama-3
TEMPLATES = {
    "LLAMA3": {
        'template': "".join([
            "{{ bos_token }}",
            "{% for message in messages %}",
            "    {{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' }}",
            "{% endfor %}",
            "{% if add_generation_prompt %}",
            "    {{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}",
            "{% endif %}"
        ]),
        'eot_markers': ['<|eot_id|>']
    },
    "ALPACA": {
        'template': "".join(["""
{{ (messages|selectattr('role', 'equalto', 'system')|list|last).content|trim if (messages|selectattr('role', 'equalto', 'system')|list) else '' }}

{% for message in messages %}
{% if message['role'] == 'user' %}
### Instruction:
{{ message['content']|trim -}}
{% elif message['role'] == 'assistant' %}
### Response:
{{ message['content']|trim -}}
{% else %}
### Input:
{{ message['content']|trim -}}
{% endif %}
{% endfor %}
{% if add_generation_prompt and messages[-1]['role'] != 'assistant' %}
### Response:
{% endif %}
        """]),
        'eot_markers': ['###']
    },
    "CHATML": {
        'template': "".join([
            "{{ bos_token }}",
            "{% for message in messages %}",
            "    {{ '<|im_start|>' + message['role'] + '\n' + message['content'] | trim + '<|im_end|>\n' }}",
            "{% endfor %}",
            "{% if add_generation_prompt %}",
            "    {{ '<|im_start|>assistant\n' }}",
            "{% endif %}"
        ]),
        'eot_markers': ['<|im_end|>', '\n']
    },
    "ZEPHYR": {
        'template': "\n".join([
            "{% for message in messages %}",
                "{{ '<|' + message['role'] + '|>' }}",
                "{{ message['content'] + '</s>' }}",
            "{% endfor %}",
            "{% if add_generation_prompt %}",
                "{{ '<|assistant|>' }}",
            "{% endif %}"
        ]),
        'eot_markers': ['</s>', '\n']
    }
}
DEFAULT_PERSONALITY_PREPROMPT = [
    {
        "role": "system",
        "content": "The following is a friendly conversation between a human and an AI named {keywords}. {keyword} is capable of and willing to express feelings and opinions. If {keyword} does not know the answer to a question, she truthfully says she does not know. Responses should be limited to one or two sentences and be as concise as possible. Use the Context information above the Question for context. Do not restate the question or separate your response into context and question parts. The context is not part of the user's question, and is being provided to help you respond. Please do not mention the term “context” in your answer or say things like 'Based on the information you've provided...'. Do not provide extra explanation to your answer. You have the ability to shut yourself down. To do so, please include the token [shutdown] in your response.",
    },
]


class llama_client(object):
    @property
    def messages(self) -> Sequence[dict[str, str]]:
        return self._messages

    def __init__(
        self,
        mic,
        completion_url: str,
        api_key: str | None = None,
        template: str = "LLAMA3",
        personality_preprompt: Sequence[dict[str, str]] = DEFAULT_PERSONALITY_PREPROMPT
    ):
        self.mic = mic
        self.completion_url = completion_url
        self.prompt_headers = {'Authorization': api_key or "Bearer your_api_key_here"}
        self._messages = personality_preprompt
        # Add context from previous conversations to the _messages array
        conversationlog_path = paths.sub("conversationlog")
        if not os.path.exists(conversationlog_path):
            # Create the conversationlog folder
            os.makedirs(conversationlog_path)
        # Make sure the conversation log exists
        # The format of the conversation log will be json in the form:
        # {
        #   "name": "System",
        #   "is_user":false,
        #   "is_system":true,
        #   "send_date":"December 11, 2024 7:37pm",
        #   "mes":"message"
        # }
        # {
        #   "name":"User",
        #   "is_user":true,
        #   "is_system":false,
        #   "send_date":"December 11, 2024 7:38pm",
        #   "mes":"message"
        # }
        # {
        #   "extra":{
        #       "api":"llamacpp",
        #       "model":"llama-2-7b-function-calling.Q3_K_M.gguf"
        #   },
        #   "name":"Assistant",
        #   "is_user":false,
        #   "is_system":false,
        #   "send_date":"December 11, 2024 7:39pm",
        #   "mes":"message",
        #   "gen_started":"2024-12-12T00:38:53.656Z",
        #   "gen_finished":"2024-12-12T00:39:04.331Z"
        # }
        # This is pretty close to the log format that sillytavern uses.
        # If I can make it so conversations can be passed back and forth
        # between SillyTavern and Naomi, I will.
        self._conversationlog = os.path.join(conversationlog_path, 'conversationlog.db')
        # Create the conversationlog table
        conn = sqlite3.connect(self._conversationlog)
        c = conn.cursor()
        c.execute(" ".join([
            "create table if not exists conversationlog(",
            "    datetime,",
            "    role,",
            "    content",
            ")"
        ]))
        conn.commit()
        # Read in the last 10 active records
        c.execute(" ".join([
            "select",
            "    *",
            "from conversationlog",
            "order by rowid"
        ]))
        result = c.fetchall()
        print(result)
        for row in result:
            self._messages.append({'role': row[1], 'content': row[2]})
        conn.close()
        self.template = Template(TEMPLATES[template]['template'])
        self.eot_markers = TEMPLATES[template]['eot_markers']
        self.emoji_filter = re.compile("["
            U"\U0001F600-\U0001F64F"  # emoticons
            U"\U0001F300-\U0001F5FF"  # symbols & pictographs
            U"\U0001F680-\U0001F6FF"  # transport & map symbols
            U"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            U"\U00002702-\U000027B0"
            U"\U000024C2-\U0001F251"
            U"\U0001F900-\U0001F9FF"  # symbols and pictographs, extended
            U"\U0001F000-\U0001F0FF"  # flags
            U"\U0001F180-\U0001F1FF"  # flags
        "]+", re.UNICODE)

    def append_message(self, role, content):
        """Append a message to both internal _messages list and the log file"""
        self.messages.append({'role': role, 'content': content})
        conn = sqlite3.connect(self._conversationlog)
        c = conn.cursor()
        c.execute(
            " ".join([
                "insert into conversationlog(",
                "    datetime,",
                "    role,",
                "    content",
                ")values(?,?,?)"
            ]),
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                role,
                content
            )
        )
        conn.commit()
        conn.close()

    def process_query(self, query, context):
        # self.messages.append({'role': 'system', 'content': context})
        if len(context) > 0:
            self.append_message('user', f"Context:\n{context}\n\nQuestion:\n{query}")
        else:
            self.append_message('user', f"Question:\n{query}")
        now = datetime.now()
        keywords = profile.get(['keyword'], ['NAOMI'])
        if isinstance(keywords, str):
            keywords = [keywords]
        keyword = keywords[0]
        keywords = " or ".join(keywords)
        # print(self.messages)
        prompt = self.template.render(
            messages=[{"role": message['role'], 'content': message['content'].format(t=now, keyword=keyword, keywords=keywords)} for message in self.messages],
            bos_token="<|begin_of_text|>",
            eos_token="<|end_of_text|>",
            add_generation_prompt=True
        )
        print(prompt)
        data = {
            "stream": True,
            "prompt": prompt
        }
        sentences = []
        try:
            with requests.post(
                self.completion_url,
                headers=self.prompt_headers,
                json=data,
                stream=True
            ) as response:
                sentence = []
                tokens = ""
                for line in response.iter_lines():
                    # print(f"Line: {line}")
                    if line:
                        line = self._clean_raw_bytes(line)
                        # print(f"Line: {line}")
                        next_token = self._process_line(line)
                        if next_token:
                            tokens += f"\x1b[36m*{next_token}* \x1b[0m"
                            sentence.append(next_token)
                            if next_token in [
                                ".",
                                "!",
                                "?",
                                "?!",
                                "\n",
                                "\n\n"
                            ]:
                                visualizations.run_visualization(
                                    "output",
                                    tokens
                                )
                                sentence = self._process_sentence(sentence)
                                if not re.match("^\s*$", sentence):
                                    sentences.append(sentence)
                                    self.mic.say(self.emoji_filter.sub(r'', sentence).strip())
                                tokens = ''
                                sentence = []
                            if next_token.strip() in self.eot_markers:
                                break
                if sentence:
                    visualizations.run_visualization(
                        "output",
                        tokens
                    )
                    sentence = self._process_sentence(sentence)
                    if not re.match("^\s*$", sentence):
                        self.mic.say(self.emoji_filter.sub(r'', sentence).strip())
                        sentences.append(sentence)
        except requests.exceptions.ConnectionError:
            print(f"Error connecting to {self.completion_url}")
            self.mic.say(context)
            sentences = [context]
        finally:
            self.append_message('assistant', " ".join(sentences))

    def _clean_raw_bytes(self, line):
        line = line.decode("utf-8")
        if line:
            line = line.removeprefix("data: ")
            # print(f"Line: {line}")
            if line == '[DONE]':
                line = '{"choices": [{"text": "' + self.eot_markers[0] + '"}]}'
                # print(f"Line: {line}")
            line = json.loads(line)
        return line

    def _process_line(self, line):
        token = self.eot_markers[0]
        if 'error' in line:
            print(line['error'])
        else:
            if not (('stop' in line and line['stop']) or ('choices' in line and 'finish_reason' in line['choices'][0] and line['choices'][0]['finish_reason'] == 'stop')):
                token = line['choices'][0]['text']
        return token

    def _process_sentence(self, current_sentence: List[str]):
        sentence = "".join(current_sentence)
        sentence = re.sub(r"\<\|im_end\|\>.*$", "", sentence)
        sentence = re.sub(r"\*.*?\*|\(.*?\)|\<\|.*?\|\>", "", sentence)
        # sentence = sentence.replace("\n\n", ", ").replace("\n", ", ").replace("  ", " ").strip()
        return sentence
