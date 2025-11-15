// Enhanced Tutorial System with Error Handling and State Management
(() => {
  'use strict';

  const TUTORIAL_CONFIG = {
    STORAGE_KEY: 'crm_tutorial_state',
    ANIMATION_DURATION: 300,
    STEP_DELAY: 500,
    AUTO_ADVANCE_DELAY: 3000
  };

  class TutorialManager {
    constructor() {
      this.currentStep = 0;
      this.isActive = false;
      this.steps = [];
      this.overlay = null;
      this.tooltip = null;
      this.userRole = null;
      this.completedTutorials = this.loadState();
      
      this.bindEvents();
      this.createElements();
    }

    loadState() {
      try {
        const saved = localStorage.getItem(TUTORIAL_CONFIG.STORAGE_KEY);
        return saved ? JSON.parse(saved) : {};
      } catch (e) {
        console.warn('Failed to load tutorial state:', e);
        return {};
      }
    }

    saveState() {
      try {
        localStorage.setItem(TUTORIAL_CONFIG.STORAGE_KEY, JSON.stringify(this.completedTutorials));
      } catch (e) {
        console.warn('Failed to save tutorial state:', e);
      }
    }

    bindEvents() {
      document.addEventListener('keydown', (e) => {
        if (!this.isActive) return;
        
        switch (e.key) {
          case 'Escape':
            this.stop();
            break;
          case 'ArrowRight':
          case ' ':
            e.preventDefault();
            this.next();
            break;
          case 'ArrowLeft':
            e.preventDefault();
            this.previous();
            break;
        }
      });

      window.addEventListener('resize', () => {
        if (this.isActive) {
          this.positionTooltip();
        }
      });
    }

    createElements() {
      // Create overlay
      this.overlay = document.createElement('div');
      this.overlay.className = 'tutorial-overlay';
      this.overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        display: none;
        backdrop-filter: blur(2px);
        transition: opacity ${TUTORIAL_CONFIG.ANIMATION_DURATION}ms ease;
        pointer-events: none;
      `;

      // Create tooltip
      this.tooltip = document.createElement('div');
      this.tooltip.className = 'tutorial-tooltip';
      this.tooltip.style.cssText = `
        position: fixed;
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        z-index: 10001;
        max-width: 320px;
        display: none;
        border: 1px solid #e2e8f0;
        transform: scale(0.9);
        transition: all ${TUTORIAL_CONFIG.ANIMATION_DURATION}ms ease;
      `;

      document.body.appendChild(this.overlay);
      document.body.appendChild(this.tooltip);
    }

    defineSteps(role) {
      const commonSteps = [
        {
          target: '.sidebar-header',
          title: 'Welcome to Competence CRM',
          content: 'This is your navigation sidebar. Here you can access all the main features of the CRM system.',
          position: 'right'
        },
        {
          target: '.stats-grid',
          title: 'Dashboard Overview',
          content: 'These cards show your key metrics at a glance. They update in real-time as you work with clients.',
          position: 'bottom'
        }
      ];

      const employeeSteps = [
        ...commonSteps,
        {
          target: '#logBtn',
          title: 'Log Activities',
          content: 'Click here to log your interactions with clients. This helps track your progress and maintain client relationships.',
          position: 'left'
        },
        {
          target: '.search-box',
          title: 'Search Clients',
          content: 'Use this search box to quickly find specific clients by name, email, or company.',
          position: 'bottom'
        },
        {
          target: 'tbody tr:first-child',
          title: 'Client Management',
          content: 'Each row shows client information. The color coding helps you prioritize: Green (good), Yellow (due soon), Red (overdue).',
          position: 'top',
          fallback: '.table-responsive'
        }
      ];

      const managerSteps = [
        ...commonSteps,
        {
          target: '.sidebar-nav a[href*="management"]',
          title: 'Team Management',
          content: 'Access team management features to assign clients, monitor performance, and manage your team.',
          position: 'right'
        },
        {
          target: '.sidebar-nav a[href*="reports"]',
          title: 'Analytics & Reports',
          content: 'View detailed analytics and generate reports to track team performance and client engagement.',
          position: 'right'
        }
      ];

      this.steps = role === 'manager' ? managerSteps : employeeSteps;
    }

    start(role) {
      try {
        this.userRole = role;
        
        // Check if tutorial was already completed
        const tutorialKey = `${role}_dashboard`;
        if (this.completedTutorials[tutorialKey]) {
          return;
        }

        this.defineSteps(role);
        
        if (this.steps.length === 0) {
          console.warn('No tutorial steps defined');
          return;
        }

        this.currentStep = 0;
        this.isActive = true;
        
        this.showOverlay();
        setTimeout(() => this.showStep(0), TUTORIAL_CONFIG.STEP_DELAY);
        
      } catch (error) {
        console.error('Failed to start tutorial:', error);
        this.handleError('Failed to start tutorial');
      }
    }

    showOverlay() {
      if (!this.overlay) return;
      this.overlay.style.display = 'block';
      this.overlay.style.opacity = '0';
      requestAnimationFrame(() => {
        if (this.overlay) this.overlay.style.opacity = '1';
      });
    }

    hideOverlay() {
      if (!this.overlay) return;
      this.overlay.style.opacity = '0';
      setTimeout(() => {
        if (this.overlay) this.overlay.style.display = 'none';
      }, TUTORIAL_CONFIG.ANIMATION_DURATION);
    }

    showStep(stepIndex) {
      try {
        if (!this.isActive) return;
        
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
          return this.complete();
        }

        const step = this.steps[stepIndex];
        const target = this.findTarget(step.target, step.fallback);
        
        if (!target) {
          console.warn(`Tutorial target not found: ${step.target}`);
          // Try to continue to next step instead of stopping
          setTimeout(() => {
            if (this.isActive && stepIndex < this.steps.length - 1) {
              this.showStep(stepIndex + 1);
            } else {
              this.complete();
            }
          }, 1000);
          return;
        }

        this.highlightElement(target);
        this.showTooltip(step, target);
        this.currentStep = stepIndex;
        
      } catch (error) {
        console.error('Failed to show tutorial step:', error);
        // Try to recover
        setTimeout(() => {
          if (this.isActive && stepIndex < this.steps.length - 1) {
            this.showStep(stepIndex + 1);
          } else {
            this.complete();
          }
        }, 1000);
      }
    }

    findTarget(selector, fallback) {
      let target = document.querySelector(selector);
      
      if (!target && fallback) {
        target = document.querySelector(fallback);
      }
      
      return target;
    }

    highlightElement(element) {
      // Remove previous highlights
      document.querySelectorAll('.tutorial-highlight').forEach(el => {
        el.classList.remove('tutorial-highlight');
      });

      // Add highlight to current element
      element.classList.add('tutorial-highlight');
      
      // Add highlight styles if not already present
      if (!document.getElementById('tutorial-styles')) {
        const styles = document.createElement('style');
        styles.id = 'tutorial-styles';
        styles.textContent = `
          .tutorial-highlight {
            position: relative;
            z-index: 10002 !important;
            box-shadow: 0 0 0 4px #3b82f6, 0 0 0 8px rgba(59, 130, 246, 0.3) !important;
            border-radius: 8px !important;
            animation: tutorial-pulse 2s infinite;
          }
          
          @keyframes tutorial-pulse {
            0%, 100% { box-shadow: 0 0 0 4px #3b82f6, 0 0 0 8px rgba(59, 130, 246, 0.3); }
            50% { box-shadow: 0 0 0 4px #3b82f6, 0 0 0 12px rgba(59, 130, 246, 0.2); }
          }
        `;
        document.head.appendChild(styles);
      }

      // Scroll element into view
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'center'
      });
    }

    showTooltip(step, target) {
      const rect = target.getBoundingClientRect();
      
      this.tooltip.innerHTML = `
        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 700; color: #1e293b;">
            ${step.title}
          </h3>
          <p style="margin: 0; color: #64748b; line-height: 1.5; font-size: 14px;">
            ${step.content}
          </p>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; gap: 8px;">
            <button class="tutorial-btn tutorial-btn-secondary" onclick="window.tutorialManager.stop()">
              Skip Tutorial
            </button>
            ${this.currentStep > 0 ? '<button class="tutorial-btn tutorial-btn-secondary" onclick="window.tutorialManager.previous()">Previous</button>' : ''}
          </div>
          
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 12px; color: #94a3b8; font-weight: 500;">
              ${this.currentStep + 1} of ${this.steps.length}
            </span>
            <button class="tutorial-btn tutorial-btn-primary" onclick="window.tutorialManager.next()">
              ${this.currentStep === this.steps.length - 1 ? 'Finish' : 'Next'}
            </button>
          </div>
        </div>
      `;

      // Add button styles if not present
      if (!document.getElementById('tutorial-button-styles')) {
        const buttonStyles = document.createElement('style');
        buttonStyles.id = 'tutorial-button-styles';
        buttonStyles.textContent = `
          .tutorial-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
          }
          
          .tutorial-btn-primary {
            background: #3b82f6;
            color: white;
          }
          
          .tutorial-btn-primary:hover {
            background: #2563eb;
            transform: translateY(-1px);
          }
          
          .tutorial-btn-secondary {
            background: #f1f5f9;
            color: #64748b;
            border: 1px solid #e2e8f0;
          }
          
          .tutorial-btn-secondary:hover {
            background: #e2e8f0;
            color: #475569;
          }
        `;
        document.head.appendChild(buttonStyles);
      }

      this.positionTooltip(step.position, rect);
      
      this.tooltip.style.display = 'block';
      requestAnimationFrame(() => {
        this.tooltip.style.transform = 'scale(1)';
        this.tooltip.style.opacity = '1';
      });
    }

    positionTooltip(position = 'bottom', targetRect) {
      if (!targetRect) return;
      
      const tooltipRect = this.tooltip.getBoundingClientRect();
      const margin = 16;
      let top, left;

      switch (position) {
        case 'top':
          top = targetRect.top - tooltipRect.height - margin;
          left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
          break;
        case 'bottom':
          top = targetRect.bottom + margin;
          left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
          break;
        case 'left':
          top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
          left = targetRect.left - tooltipRect.width - margin;
          break;
        case 'right':
          top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
          left = targetRect.right + margin;
          break;
        default:
          top = targetRect.bottom + margin;
          left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
      }

      // Keep tooltip within viewport
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      
      if (left < margin) left = margin;
      if (left + tooltipRect.width > viewportWidth - margin) {
        left = viewportWidth - tooltipRect.width - margin;
      }
      
      if (top < margin) top = margin;
      if (top + tooltipRect.height > viewportHeight - margin) {
        top = viewportHeight - tooltipRect.height - margin;
      }

      this.tooltip.style.top = `${top}px`;
      this.tooltip.style.left = `${left}px`;
    }

    next() {
      if (this.currentStep < this.steps.length - 1) {
        this.showStep(this.currentStep + 1);
      } else {
        this.complete();
      }
    }

    previous() {
      if (this.currentStep > 0) {
        this.showStep(this.currentStep - 1);
      }
    }

    complete() {
      try {
        // Mark tutorial as completed
        if (this.userRole) {
          const tutorialKey = `${this.userRole}_dashboard`;
          this.completedTutorials[tutorialKey] = true;
          this.saveState();
        }

        this.stop();
        
        // Show completion message
        this.showCompletionMessage();
        
      } catch (error) {
        console.error('Failed to complete tutorial:', error);
        this.stop();
      }
    }

    showCompletionMessage() {
      const message = document.createElement('div');
      message.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10003;
        font-weight: 500;
        animation: slideInRight 0.3s ease;
      `;
      
      message.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
          <i class="fas fa-check-circle"></i>
          Tutorial completed! You're ready to use the CRM.
        </div>
      `;

      // Add animation styles
      if (!document.getElementById('completion-animation')) {
        const animationStyles = document.createElement('style');
        animationStyles.id = 'completion-animation';
        animationStyles.textContent = `
          @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
        `;
        document.head.appendChild(animationStyles);
      }

      document.body.appendChild(message);
      
      setTimeout(() => {
        message.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => message.remove(), 300);
      }, 3000);
    }

    stop() {
      try {
        this.isActive = false;
        
        // Hide tooltip
        if (this.tooltip) {
          this.tooltip.style.transform = 'scale(0.9)';
          this.tooltip.style.opacity = '0';
          setTimeout(() => {
            if (this.tooltip) this.tooltip.style.display = 'none';
          }, TUTORIAL_CONFIG.ANIMATION_DURATION);
        }

        // Hide overlay
        this.hideOverlay();

        // Remove highlights
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
          el.classList.remove('tutorial-highlight');
        });

        // Ensure body is clickable
        document.body.style.pointerEvents = 'auto';
        
      } catch (error) {
        console.error('Failed to stop tutorial:', error);
        // Force cleanup
        if (this.overlay) this.overlay.style.display = 'none';
        if (this.tooltip) this.tooltip.style.display = 'none';
        document.body.style.pointerEvents = 'auto';
      }
    }

    handleError(message) {
      console.error('Tutorial Error:', message);
      this.stop();
      
      // Show user-friendly error message
      if (window.showAlert) {
        window.showAlert('Tutorial encountered an error and was stopped.', 'warning');
      }
    }

    restart(role) {
      if (role) {
        const tutorialKey = `${role}_dashboard`;
        delete this.completedTutorials[tutorialKey];
        this.saveState();
      }
      
      this.stop();
      setTimeout(() => this.start(role), 500);
    }
  }

  // Create global instance
  window.tutorialManager = new TutorialManager();

  // Legacy function for backward compatibility
  window.startTutorial = (role) => {
    window.tutorialManager.start(role);
  };

  // Expose restart function
  window.restartTutorial = (role) => {
    window.tutorialManager.restart(role);
  };

})();