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

    // Check if step is accessible
    const hasTaskId = urlTaskId || taskId;
    if (stepNumber === 2 && !hasTaskId) return 'disabled';
    if (stepNumber === 3 && (!hasTaskId || status !== 'script_ready')) return 'disabled';
    if (stepNumber === 4 && (!hasTaskId || status !== 'script_ready' && status !== 'generating_video')) return 'disabled';
    if (stepNumber === 5 && status !== 'completed') return 'disabled';

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <nav className="navigation">
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
                  {stepStatus === 'completed' ? '✓' : step.step}
                </div>
                <div className="step-label">{step.label}</div>
              </Link>
              {index < steps.length - 1 && (
                <div className={`step-connector ${stepStatus === 'completed' ? 'completed' : ''}`} />
              )}
            </div>
          );
        })}
      </div>
    </nav>
  );
}

export default Navigation;

