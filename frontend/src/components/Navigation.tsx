import { Link, useLocation } from 'react-router-dom';
import { useTaskStore } from '@/store/useTaskStore';
import './Navigation.css';

function Navigation() {
  const location = useLocation();
  const { taskId, status } = useTaskStore();

  // Get task ID from URL if available
  const urlTaskId = location.pathname.match(/\/task\/([^/]+)/)?.[1] || taskId;

  const getStepPath = (step: number): string => {
    if (urlTaskId) {
      const paths = ['upload', 'script', 'optimize', 'video', 'download'];
      return `/task/${urlTaskId}/${paths[step - 1]}`;
    }
    const paths = ['/upload', '/script', '/optimize', '/video', '/download'];
    return paths[step - 1];
  };

  const steps = [
    { path: getStepPath(1), label: '上傳檔案', step: 1 },
    { path: getStepPath(2), label: '生成腳本', step: 2 },
    { path: getStepPath(3), label: '優化腳本', step: 3 },
    { path: getStepPath(4), label: '生成影片', step: 4 },
    { path: getStepPath(5), label: '下載影片', step: 5 },
  ];

  const getStepStatus = (stepPath: string, stepNumber: number): 'completed' | 'active' | 'pending' | 'disabled' => {
    const currentPath = location.pathname;
    const currentIndex = steps.findIndex(s => {
      // Match exact path or match task ID pattern
      return s.path === currentPath || 
             (currentPath.includes('/task/') && currentPath.endsWith(s.path.split('/').pop() || ''));
    });
    const stepIndex = steps.findIndex(s => s.path === stepPath);

    // Check if step is completed based on task status
    const hasTaskId = urlTaskId || taskId;
    
    // Step 1 (Upload) is completed if we have a task ID
    if (stepNumber === 1 && hasTaskId) {
      return stepIndex === currentIndex ? 'active' : 'completed';
    }
    
    // Step 2 (Generate Script) is completed if script is ready or beyond
    if (stepNumber === 2 && (status === 'script_ready' || status === 'generating_video' || status === 'completed')) {
      return stepIndex === currentIndex ? 'active' : 'completed';
    }
    
    // Step 3 (Optimize Script) is completed if we've moved to video generation or completed
    if (stepNumber === 3 && (status === 'generating_video' || status === 'completed')) {
      return stepIndex === currentIndex ? 'active' : 'completed';
    }
    
    // Step 4 (Generate Video) is completed if video is completed
    if (stepNumber === 4 && status === 'completed') {
      return stepIndex === currentIndex ? 'active' : 'completed';
    }

    // Check if step is accessible (disabled)
    if (stepNumber === 2 && !hasTaskId) return 'disabled';
    if (stepNumber === 3 && (!hasTaskId || (status !== 'script_ready' && status !== 'generating_video' && status !== 'completed'))) return 'disabled';
    if (stepNumber === 4 && (!hasTaskId || (status !== 'script_ready' && status !== 'generating_video' && status !== 'completed'))) return 'disabled';
    if (stepNumber === 5 && status !== 'completed') return 'disabled';

    // If on current step, mark as active
    if (stepIndex === currentIndex) return 'active';
    
    // Otherwise pending
    return 'pending';
  };

  return (
    <nav className="navigation">
      <Link to="/" className="home-button" title="回到首頁">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      </Link>
      <div className="nav-steps">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.path, step.step);
          const isDisabled = stepStatus === 'disabled';

          return (
            <div key={step.path} className="nav-step-container">
              <Link
                to={step.path}
                className={`nav-step ${stepStatus} ${isDisabled ? 'disabled' : ''}`}
                onClick={(e) => {
                  if (isDisabled) {
                    e.preventDefault();
                  }
                }}
              >
                <div className="step-number">
                  {stepStatus === 'completed' ? (
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '28px', height: '28px', strokeWidth: 3.5 }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.step
                  )}
                </div>
                <div className="step-label">{step.label}</div>
              </Link>
            </div>
          );
        })}
      </div>
    </nav>
  );
}

export default Navigation;

