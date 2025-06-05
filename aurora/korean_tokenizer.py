from rasa.nlu.components import Component
from rasa.nlu.tokenizers.tokenizer import Tokenizer
from rasa.nlu.training_data import Message
from typing import Any, List, Text, Dict, Type

# KoNLPy Okt 임포트
from konlpy.tag import Okt

class KoNLPyOktTokenizer(Tokenizer): # Tokenizer 클래스를 상속받습니다.
    
    defaults = {
        "dictionary_path": None # 사용자 사전 경로 (선택 사항)
    }

    def __init__(self, component_config: Dict[Text, Any] = None) -> None:
        super().__init__(component_config)
        self.okt = Okt()
        # 사용자 사전이 있다면 여기서 로드할 수 있습니다.
        # if self.component_config.get("dictionary_path"):
        #     # 사전 로드 로직 추가
        #     pass

    @classmethod
    def required_packages(cls: Type["KoNLPyOktTokenizer"]) -> List[Text]:
        return ["konlpy"]

    def tokenize(self, message: Message, attribute: Text) -> List[Text]:
        text = message.get(attribute)
        
        # Okt를 사용하여 형태소 분석 및 토큰화 (여기서는 형태소 단위로)
        # words = self.okt.morphs(text) 
        # 또는 품사 정보와 함께 (더 많은 정보 활용 가능)
        # tokenized = self.okt.pos(text, stem=True) # stem=True는 어간 추출
        # tokens = [word for word, tag in tokenized]
        
        # 일반적인 토큰화 (명사, 동사, 형용사 등 의미있는 품사 위주 또는 전체 형태소)
        # 여기서는 간단히 형태소(morphs)를 사용하거나, 명사만 추출하는 등의 전략을 사용할 수 있습니다.
        # 더 정교하게 하려면 특정 품사만 선택하거나, 불용어를 제거하는 로직을 추가할 수 있습니다.
        tokens_with_pos = self.okt.pos(text, norm=True, stem=True) # 정규화, 어간추출
        
        # 토큰 객체 생성 (Rasa NLU가 이해할 수 있는 형태)
        # 각 토큰은 시작 위치(offset)와 텍스트 값을 가집니다.
        # 정확한 offset 계산은 복잡할 수 있으므로, 여기서는 단순화된 예시를 보여드립니다.
        # 실제 구현에서는 토큰의 원본 텍스트 내 시작 위치를 정확히 추적해야 합니다.
        
        # 가장 간단한 방법은 Okt가 분리한 텍스트 조각들을 사용하는 것입니다.
        # 하지만 DIETClassifier 등은 토큰의 시작/끝 오프셋 정보를 사용하므로,
        # 정확한 오프셋 정보가 중요합니다.
        
        # 여기서는 우선 형태소 텍스트 리스트를 반환하고,
        # Rasa가 내부적으로 이를 처리하도록 합니다. (더 나은 방법은 Token 클래스 사용)
        processed_tokens = [word for word, tag in tokens_with_pos]

        # message.set("tokens", self._convert_words_to_tokens(processed_tokens, text))
        # Tokenizer 클래스를 상속받으면 tokenize 메소드는 List[Token]을 반환해야 합니다.
        # 아래는 _convert_to_rasa_tokens 헬퍼 함수를 사용한 예시입니다.
        return self._convert_to_rasa_tokens(tokens_with_pos, text)

    # 헬퍼 함수 추가 (Okt의 출력 (단어, 품사) 리스트를 Rasa의 Token 객체 리스트로 변환)
    def _convert_to_rasa_tokens(self, tokens_with_pos: List[tuple[Text, Text]], text: Text) -> List[Token]:
        from rasa.nlu.tokenizers.token import Token

        rasa_tokens = []
        current_offset = 0
        for word, tag in tokens_with_pos:
            # 원본 텍스트에서 현재 단어의 시작 위치 찾기 (단순 예시)
            # 실제로는 더 정교한 오프셋 계산 필요
            try:
                word_offset = text.index(word, current_offset)
            except ValueError: # 단어를 찾지 못한 경우 (변형 등으로 인해)
                # 이 경우, 그냥 현재 오프셋을 사용하거나 다른 방식으로 처리
                word_offset = current_offset 
                # print(f"Warning: Could not find exact offset for token '{word}' in text: '{text}' starting from offset {current_offset}")

            rasa_tokens.append(Token(word, word_offset, data={"pos": tag}))
            current_offset = word_offset + len(word)
            
        return rasa_tokens