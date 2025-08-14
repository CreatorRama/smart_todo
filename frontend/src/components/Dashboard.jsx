import { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  BarChart3,
  TrendingUp,
  Calendar,
  Target
} from 'lucide-react';
import { tasksAPI } from '../lib/api';

const StatCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend }) => (
  <div className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow duration-200">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className={`text-3xl font-bold text-${color}-600 mt-2`}>{value}</p>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        {trend && (
          <div className={`flex items-center mt-2 text-sm ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
            <TrendingUp className={`w-4 h-4 mr-1 ${trend.positive ? '' : 'rotate-180'}`} />
            {trend.value}
          </div>
        )}
      </div>
      <div className={`p-3 rounded-xl bg-${color}-100`}>
        <Icon className={`w-8 h-8 text-${color}-600`} />
      </div>
    </div>
  </div>
);

const Dashboard = ({ className = '' }) => {
  const [statistics, setStatistics] = useState(null);
  const [priorityDistribution, setPriorityDistribution] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [statsRes, priorityRes] = await Promise.all([
          tasksAPI.getStatistics(),
          tasksAPI.getPriorityDistribution()
        ]);
        setStatistics(statsRes.data);
        setPriorityDistribution(priorityRes.data);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="w-12 h-12 bg-gray-200 rounded-xl"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Tasks"
          value={statistics?.total_tasks || 0}
          icon={Target}
          color="blue"
        />
        
        <StatCard
          title="Completed"
          value={statistics?.completed_tasks || 0}
          subtitle={`${(statistics?.completion_rate || 0).toFixed(1)}% completion rate`}
          icon={CheckCircle2}
          color="green"
        />
        
        <StatCard
          title="In Progress"
          value={statistics?.in_progress_tasks || 0}
          subtitle={`${statistics?.pending_tasks || 0} pending`}
          icon={Clock}
          color="yellow"
        />
        
        <StatCard
          title="Overdue"
          value={statistics?.overdue_tasks || 0}
          subtitle="Need attention"
          icon={AlertTriangle}
          color="red"
        />
      </div>

      {/* Priority Distribution */}
      {priorityDistribution && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center mb-4">
              <BarChart3 className="w-5 h-5 text-gray-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Task Priority Distribution</h3>
            </div>
            
            <div className="space-y-4">
              {Object.entries(priorityDistribution).map(([priority, count]) => {
                const total = Object.values(priorityDistribution).reduce((sum, val) => sum + val, 0);
                const percentage = total > 0 ? (count / total) * 100 : 0;
                
                const colors = {
                  low: 'bg-green-500',
                  medium: 'bg-yellow-500',
                  high: 'bg-orange-500',
                  urgent: 'bg-red-500'
                };
                
                return (
                  <div key={priority} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full ${colors[priority] || 'bg-gray-500'} mr-3`}></div>
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {priority}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{count}</span>
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${colors[priority] || 'bg-gray-500'}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500 w-10 text-right">
                        {percentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center mb-4">
              <Calendar className="w-5 h-5 text-gray-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Quick Insights</h3>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Productivity Tip</h4>
                <p className="text-sm text-blue-700">
                  {statistics?.completion_rate > 70 
                    ? "Great job! You're maintaining excellent productivity." 
                    : statistics?.completion_rate > 50
                    ? "Good progress! Consider prioritizing high-impact tasks."
                    : "Focus on completing smaller tasks first to build momentum."
                  }
                </p>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Achievement</h4>
                <p className="text-sm text-green-700">
                  You've completed {statistics?.completed_tasks || 0} tasks! 
                  {statistics?.completed_tasks > 10 && " You're on a roll! 🎉"}
                </p>
              </div>
              
              {statistics?.overdue_tasks > 0 && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <h4 className="font-medium text-red-900 mb-2">Action Needed</h4>
                  <p className="text-sm text-red-700">
                    You have {statistics.overdue_tasks} overdue task{statistics.overdue_tasks > 1 ? 's' : ''}. 
                    Consider updating deadlines or prioritizing these tasks.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;