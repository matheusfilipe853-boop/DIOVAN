"""
DIOVAN — Interface Base (Contrato Abstrato)
Qualquer interface que o DIOVAN usar herda daqui.
O DIOVAN não sabe qual interface está usando.
"""

from abc import ABC, abstractmethod

class BaseInterface(ABC):

    @abstractmethod
    def start(self, on_input, on_exit):
        """
        Inicia a interface.
        on_input: callback chamado quando usuário envia mensagem
        on_exit: callback chamado quando usuário encerra
        """
        pass

    @abstractmethod
    def render_response(self, text: str):
        """Renderiza resposta do DIOVAN"""
        pass

    @abstractmethod
    def render_status(self, text: str):
        """Renderiza mensagem de status (processando, buscando, etc)"""
        pass

    @abstractmethod
    def render_error(self, text: str):
        """Renderiza erro"""
        pass
