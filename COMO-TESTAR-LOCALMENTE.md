# Testar a conversa com IA no seu computador

1. Abra `Abrir teste local.bat`. Uma janela preta ficará aberta enquanto o teste estiver rodando; feche-a para parar.
2. O navegador abrirá o site em `http://127.0.0.1:8000`.
3. Se a página avisar que falta o modelo, abra o PowerShell e rode:

   ```powershell
   & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull qwen3:1.7b
   ```

   O download ocupa cerca de 1,4 GB. Depois que terminar, atualize a página.
4. Escolha um tipo de negócio e faça perguntas no chat. Ele usa os serviços e horários fictícios da demonstração. Agendamentos não são gravados nem confirmados numa agenda real.

O site publicado continua usando a demonstração roteirizada. O modelo é acessado somente pelo endereço local deste computador; não envie dados reais de clientes neste protótipo.
