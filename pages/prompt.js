export async function renderPrompt() {
  // Extract slug from pathname
  const slug = location.pathname.split('/').pop().replace('.html', '');
  const basePath = window.location.pathname.startsWith('/strudel-jam/') ? '/strudel-jam' : '';
  
  try {
    const index = await (await fetch(`${basePath}/data/index.json`)).json();
    const entry = index.find(p => p.promptSlug === slug);
    
    if (!entry) {
      document.getElementById('model-grid').innerHTML = 
        '<div class="text-center bg-red-100 border-2 border-red-500 p-4 font-mono">ERROR: PROMPT_NOT_FOUND.DAT</div>';
      return;
    }

    // Set title and prompt text
    document.getElementById('prompt-title').textContent = entry.title.replace(/\s+/g, '_').toUpperCase();
    document.title = `STRUDEL-JAM.EXE - ${entry.title.toUpperCase()}`;
    
    // Try to load prompt text
    try {
      const promptPath = `${basePath}/prompts/${slug}.md`;
      const promptText = await (await fetch(promptPath)).text();
      document.getElementById('prompt-text').textContent = promptText;
    } catch (e) {
      document.getElementById('prompt-text').textContent = 'NO_PROMPT_FILE_FOUND.TXT';
    }

    const grid = document.getElementById('model-grid');
    const workspace = document.getElementById('desktop-workspace');
    
    // Calculate optimal window arrangement for any number of models
    const modelCount = entry.models.length;
    const workspaceWidth = workspace.clientWidth || 1200; // fallback
    const workspaceHeight = workspace.clientHeight || 600; // fallback
    
    // Determine window size based on number of models - ensure minimum width for Strudel controls
    let windowWidth, windowHeight, cols, rows;
    
    if (modelCount <= 2) {
      // Large windows for very few models
      windowWidth = 750;
      windowHeight = 550;
      cols = Math.min(2, modelCount);
      rows = Math.ceil(modelCount / cols);
    } else if (modelCount <= 4) {
      // Good sized windows for few models
      windowWidth = 720;
      windowHeight = 520;
      cols = 2;
      rows = Math.ceil(modelCount / cols);
    } else if (modelCount <= 6) {
      // Medium windows - still comfortable
      windowWidth = 690;
      windowHeight = 500;
      cols = 2;
      rows = Math.ceil(modelCount / cols);
    } else if (modelCount <= 9) {
      // Smaller but still functional windows - minimum for strudel controls
      windowWidth = 660;
      windowHeight = 480;
      cols = 3;
      rows = Math.ceil(modelCount / cols);
    } else {
      // Minimum size to ensure strudel controls are fully visible - never go below 630px width
      windowWidth = 630;
      windowHeight = 460;
      cols = Math.min(3, Math.ceil(Math.sqrt(modelCount * 0.75))); // Prefer fewer columns
      rows = Math.ceil(modelCount / cols);
    }
    
    // Calculate spacing - allow for scrolling if needed
    const horizontalSpacing = Math.max(15, (workspaceWidth - (cols * windowWidth)) / (cols + 1));
    const verticalSpacing = Math.max(15, Math.min(30, (workspaceHeight - (rows * windowHeight)) / (rows + 1)));
    
    // Generate positions in a grid
    const calculatePosition = (index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      
      const x = horizontalSpacing + col * (windowWidth + horizontalSpacing);
      const y = verticalSpacing + row * (windowHeight + verticalSpacing);
      
      // Add slight randomization to avoid perfect grid look
      const jitterX = (Math.random() - 0.5) * 15;
      const jitterY = (Math.random() - 0.5) * 15;
      
      return {
        x: Math.max(10, x + jitterX),
        y: Math.max(10, y + jitterY)
      };
    };
    
    // Auto-arrange button for manual reorganization
    const autoArrangeBtn = document.createElement('button');
    autoArrangeBtn.className = 'absolute top-2 right-2 bg-gray-300 border-2 border-gray-500 px-3 py-1 text-xs font-mono hover:bg-gray-200 z-40';
    autoArrangeBtn.textContent = '[AUTO-ARRANGE]';
    autoArrangeBtn.onclick = () => {
      const windows = workspace.querySelectorAll('.model-window');
      windows.forEach((win, idx) => {
        const pos = calculatePosition(idx);
        win.style.left = pos.x + 'px';
        win.style.top = pos.y + 'px';
        win.style.transition = 'all 0.5s ease-out';
        setTimeout(() => {
          win.style.transition = '';
        }, 500);
      });
    };
    workspace.appendChild(autoArrangeBtn);
    
    // Ensure workspace can scroll if needed for many windows
    if (rows * (windowHeight + verticalSpacing) > workspaceHeight) {
      workspace.style.height = (rows * (windowHeight + verticalSpacing) + 50) + 'px';
      workspace.style.overflowY = 'auto';
    }
    
    entry.models.forEach((m, index) => {
      const windowDiv = document.createElement('div');
      windowDiv.className = `
        model-window absolute bg-win-gray border-2 border-gray-400 shadow-lg
        font-mono
      `;
      
      // Set dynamic size
      windowDiv.style.width = windowWidth + 'px';
      windowDiv.style.height = windowHeight + 'px';
      
      const pos = calculatePosition(index);
      windowDiv.style.left = pos.x + 'px';
      windowDiv.style.top = pos.y + 'px';
      
      // Calculate REPL height based on window size - ensure good proportion
      const replHeight = Math.max(250, windowHeight - 180);
      
      windowDiv.innerHTML = `
        <!-- Window title bar -->
        <div class="model-title bg-gradient-to-r from-blue-500 to-blue-600 text-white px-2 py-1 flex items-center justify-between border-b border-gray-400 cursor-move">
          <div class="flex items-center space-x-2">
            <div class="w-4 h-4 bg-white border border-gray-400 flex items-center justify-center text-xs font-bold text-black">AI</div>
            <span class="font-system text-sm truncate">${m.name.toUpperCase()}.EXE</span>
          </div>
          <div class="flex space-x-1">
            <div class="w-4 h-4 bg-gray-300 border border-gray-600 text-xs flex items-center justify-center cursor-pointer hover:bg-gray-200">_</div>
            <div class="w-4 h-4 bg-gray-300 border border-gray-600 text-xs flex items-center justify-center cursor-pointer hover:bg-gray-200">□</div>
            <div class="w-4 h-4 bg-red-500 border border-gray-600 text-xs flex items-center justify-center text-white cursor-pointer hover:bg-red-400">×</div>
          </div>
        </div>
        
        <!-- Resize handles -->
        <div class="resize-handle se"></div>
        <div class="resize-handle e"></div>
        <div class="resize-handle s"></div>
        
        <!-- Window content -->
        <div class="bg-white p-3 h-full overflow-hidden flex flex-col">
          <!-- Status bar with blinking cursor -->
          <div class="bg-gray-200 border border-gray-400 p-2 text-xs font-mono mb-3 flex justify-between">
            <span class="truncate">${m.name}</span>
            <span class="status-badge flex-shrink-0"></span>
          </div>
          
          <!-- System messages -->
          <div class="bg-black border border-gray-500 p-2 text-xs font-mono text-green-400 mb-3 h-14 overflow-hidden">
            <div class="system-messages">
              <div class="truncate">INIT_AI_MODULE.SYS...</div>
              <div class="truncate">LOAD_NETWORKS... <span class="blink">█</span></div>
            </div>
          </div>
          
          <!-- Audio section - flexible height -->
          <div class="flex-1 flex flex-col mb-3">
            <div class="bg-black border border-gray-500 p-2 text-xs font-mono text-green-400 mb-2 flex justify-between">
              <span class="truncate">AUDIO_SYNTH.EXE</span>
              <span class="audio-status">READY</span>
            </div>
            <div class="repl-container bg-black border-2 border-gray-500 flex-1 p-2 relative overflow-hidden" style="min-height: ${replHeight}px;">
              <!-- Old-school scanlines effect -->
              <div class="absolute inset-0 pointer-events-none">
                <div class="scanlines"></div>
              </div>
            </div>
          </div>
          
          <!-- Controls -->
          <div class="flex space-x-2 mb-3">
            <button class="minimize-btn bg-gray-300 border border-gray-500 px-3 py-1 text-xs font-mono hover:bg-gray-200 flex-1">
              [MIN]
            </button>
            <button class="code-btn bg-gray-300 border border-gray-500 px-3 py-1 text-xs font-mono hover:bg-gray-200 flex-1">
              [CODE]
            </button>
            <div class="text-xs font-mono text-gray-600 flex items-center px-2">
              CPU: <span class="cpu-usage text-green-600">12%</span>
            </div>
          </div>
          
          <!-- Code section -->
          <div class="code-section hidden border-t border-gray-400 pt-3 max-h-32 overflow-y-auto">
            <div class="bg-gray-100 border border-gray-400 p-3">
              <div class="text-xs font-mono text-gray-600 mb-2">
                ${m.name.toLowerCase()}_output.strl | <span class="file-size">0KB</span>
              </div>
              <pre class="code-container text-xs font-mono">
                <code class="text-black"></code>
              </pre>
            </div>
          </div>
        </div>
      `;
      
      const replContainer = windowDiv.querySelector('.repl-container');
      const codeElement = windowDiv.querySelector('code');
      const statusBadge = windowDiv.querySelector('.status-badge');
      const audioStatus = windowDiv.querySelector('.audio-status');
      const codeSection = windowDiv.querySelector('.code-section');
      const codeBtn = windowDiv.querySelector('.code-btn');
      const minimizeBtn = windowDiv.querySelector('.minimize-btn');
      const systemMessages = windowDiv.querySelector('.system-messages');
      const cpuUsage = windowDiv.querySelector('.cpu-usage');
      const fileSize = windowDiv.querySelector('.file-size');
      
      // Add CSS for old-school effects
      if (!document.querySelector('#retro-styles')) {
        const style = document.createElement('style');
        style.id = 'retro-styles';
        style.textContent = `
          .blink { animation: blink 1s infinite; }
          @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
          
          .scanlines {
            background: linear-gradient(transparent 50%, rgba(0, 255, 0, 0.03) 50%);
            background-size: 100% 4px;
            animation: scan 0.1s linear infinite;
          }
          @keyframes scan { 0% { background-position: 0 0; } 100% { background-position: 0 4px; } }
          
          .flicker { animation: flicker 3s infinite; }
          @keyframes flicker { 0%, 98% { opacity: 1; } 99% { opacity: 0.8; } 100% { opacity: 1; } }
        `;
        document.head.appendChild(style);
      }
      
      // Simplified system message cycling for performance
      const messages = ['NET_INIT.OK', 'LOAD_ENGINE...', 'BUF_ALLOC', 'SYN_READY', 'WAIT_INPUT', 'PROC_PROMPT'];
      let messageIndex = 0;
      const messageInterval = setInterval(() => {
        const lines = systemMessages.children;
        if (lines.length >= 2) {
          lines[0].innerHTML = `<span class="truncate">${lines[1].textContent}</span>`;
          lines[1].innerHTML = `<span class="truncate">${messages[messageIndex]} <span class="blink">█</span></span>`;
          messageIndex = (messageIndex + 1) % messages.length;
        }
      }, 3000 + Math.random() * 2000); // Stagger intervals
      
      // Less frequent resource monitoring for performance
      setInterval(() => {
        const cpu = Math.floor(Math.random() * 30 + 5);
        cpuUsage.textContent = cpu + '%';
      }, 5000 + Math.random() * 3000);
      
      // Code toggle functionality
      codeBtn.addEventListener('click', () => {
        codeSection.classList.toggle('hidden');
        codeBtn.textContent = codeSection.classList.contains('hidden') ? '[CODE]' : '[HIDE]';
      });
      
      // Minimize REPL functionality
      let replMinimized = false;
      minimizeBtn.addEventListener('click', () => {
        if (replMinimized) {
          replContainer.style.minHeight = replHeight + 'px';
          replContainer.style.height = 'auto';
          minimizeBtn.textContent = '[MIN]';
          replMinimized = false;
        } else {
          replContainer.style.minHeight = '50px';
          replContainer.style.height = '50px';
          minimizeBtn.textContent = '[MAX]';
          replMinimized = true;
        }
      });
      
      // Fetch model data
      fetch(`${basePath}/data/${m.card}`)
        .then(response => {
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${m.card}`);
          return response.json();
        })
        .then(cardData => {
          if (cardData.success) {
            statusBadge.innerHTML = '<span class="bg-green-500 text-white px-2 py-1 border border-green-700 flicker text-xs">OK</span>';
            audioStatus.textContent = 'READY';
            
            // Load Strudel embed
            replContainer.innerHTML = `
              <div class="absolute inset-0 pointer-events-none">
                <div class="scanlines"></div>
              </div>
              <strudel-repl 
                code="${cardData.code.replace(/"/g, '&quot;').replace(/`/g, '\\`')}"
                autoplay>
              </strudel-repl>
            `;
            
            // Set code content and file size
            codeElement.textContent = cardData.code;
            fileSize.textContent = Math.ceil(cardData.code.length / 1024) + 'KB';
          } else {
            statusBadge.innerHTML = '<span class="bg-red-500 text-white px-2 py-1 border border-red-700 blink text-xs">ERR</span>';
            audioStatus.textContent = 'FAIL';
            
            replContainer.innerHTML = `
              <div class="absolute inset-0 pointer-events-none">
                <div class="scanlines"></div>
              </div>
              <div class="flex items-center justify-center h-full text-red-400 font-mono">
                <div class="text-center border border-red-500 bg-red-900/20 p-3">
                  <div class="text-sm mb-1 blink">ERROR</div>
                  <div class="text-xs">NEURAL_FAULT</div>
                </div>
              </div>
            `;
            
            codeElement.textContent = cardData.rawResponse || 'NO_RESPONSE_DATA.TXT';
            fileSize.textContent = '0KB';
          }
        }).catch(e => {
          statusBadge.innerHTML = '<span class="bg-yellow-500 text-black px-2 py-1 border border-yellow-700 blink text-xs">WARN</span>';
          audioStatus.textContent = 'NET_ERR';
          
          replContainer.innerHTML = `
            <div class="absolute inset-0 pointer-events-none">
              <div class="scanlines"></div>
            </div>
            <div class="flex items-center justify-center h-full text-yellow-400 font-mono">
              <div class="text-center border border-yellow-500 bg-yellow-900/20 p-3">
                <div class="text-sm mb-1 blink">TIMEOUT</div>
                <div class="text-xs">RETRY: 3/3</div>
              </div>
            </div>
          `;
        });
      
      // Add window to workspace immediately
      workspace.appendChild(windowDiv);
    });
    
  } catch (e) {
    document.getElementById('model-grid').innerHTML = 
      '<div class="text-center bg-red-100 border-2 border-red-500 p-4 font-mono">CRITICAL_ERROR: UNABLE_TO_LOAD_EXPERIMENT_DATA.DAT</div>';
  }
} 