import json
import re
import requests
from datetime import datetime
from jinja2 import Template
from naomi import profile
from typing import List, Sequence


LLM_STOP_SEQUENCE = "<|eot_id|>"  # End of sentence token for Meta-Llama-3
TEMPLATES = {
    "LLAMA3": "".join([
        "{{ bos_token }}",
        "{% for message in messages %}",
        "    {{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' }}",
        "{% endfor %}",
        "{% if add_generation_prompt %}",
        "    {{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}",
        "{% endif %}"
    ]),
    "CHATML": "".join([
        "{{ bos_token }}",
        "{% for message in messages %}",
        "    {{ '<|im_start|>' + message['role'] + '\n' + message['content'] | trim + '<|im_end|>\n' }}",
        "{% endfor %}",
        "{% if add_generation_prompt %}",
        "    {{ '<|im_start|>assistant\n' }}",
        "{% endif %}"
    ])
}
DEFAULT_PERSONALITY_PREPROMPT = [
    {
        "role": "system",
        "content": "The following is a friendly conversation between a human and an AI named {keywords}. If {keywords} does not know the answer to a question, she truthfully says she does not know. Responses should be limited to one or two sentences and be as concise as possible. The following information has been provided by {keywords} and may be used to answer the request, but only if appropriate: {context}",
    },
]


class llama_client:
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
        self.template = Template(TEMPLATES[template])

    def process_query(self, query, context):
        self.messages.append({'role': 'user', 'content': query})
        now = datetime.now()
        keywords = profile.get(['keyword'], ['NAOMI'])
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords = " or ".join(keywords)
        # print(self.messages)
        prompt = self.template.render(
            messages=[{"role": message['role'], 'content': message['content'].format(t=now, context=context, keywords=keywords)} for message in self.messages],
            bos_token="<|begin_of_text|>",
            eos_token="<|end_of_text|>",
            add_generation_prompt=True
        )
        # print(prompt)
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
                for line in response.iter_lines():
                    if line:
                        line = self._clean_raw_bytes(line)
                        next_token = self._process_line(line)
                        if next_token:
                            sentence.append(next_token)
                            if next_token in [
                                ".",
                                "!",
                                "?",
                                "?!",
                                "\n",
                                "\n\n"
                            ]:
                                sentence = self._process_sentence(sentence)
                                sentences.append(sentence)
                                self.mic.say(sentence)
                                sentence = []
                            if next_token == "<|im_end|>":
                                break
                if sentence:
                    sentence = self._process_sentence(sentence)
                    self.mic.say(sentence)
                    sentences.append(sentence)
        except requests.exceptions.ConnectionError:
            self.mic.say(context)
            sentences = [context]
        self.messages.append({"role": "assistant", "content": " ".join(sentences)})

    def _clean_raw_bytes(self, line):
        line = line.decode("utf-8")
        line = line.removeprefix("data: ")
        line = json.loads(line)
        return line

    def _process_line(self, line):
        if 'error' in line:
            print(line['error'])
        else:
            if not line['stop']:
                token = line['content']
                return token

    def _process_sentence(self, current_sentence: List[str]):
        sentence = "".join(current_sentence).strip()
        sentence = re.sub(r"\<\|im_end\|\>.*$", "", sentence)
        sentence = re.sub(r"\*.*?\*|\(.*?\)|\<\|.*?\|\>", "", sentence)
        sentence = sentence.replace("\n\n", ", ").replace("\n", ", ").replace("  ", " ")
        return sentence
