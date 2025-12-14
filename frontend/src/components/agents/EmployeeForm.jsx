import React, { useState } from 'react';
import { Send, Loader2, User, Briefcase, ChevronDown } from 'lucide-react';
import { runEmployeeAgent } from '../../services/api';

const ROLES = [
  { id: 'engineer', label: 'Engineer', icon: User, description: 'Create PRs, review code' },
  { id: 'manager', label: 'Manager', icon: Briefcase, description: 'Send messages, status updates' },
];

const TASK_SUGGESTIONS = {
  engineer: [
    'implement payment retry for ENG-500',
    'review the PR that adds rate limiting',
    'fix the database connection issue',
  ],
  manager: [
    'send slack message about the bug fix',
    'give status update on payment incident',
    'notify team about deployment schedule',
  ],
};

export default function EmployeeForm({ onResponse, isLoading, setIsLoading }) {
  const [role, setRole] = useState('engineer');
  const [task, setTask] = useState('');
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);
  const dropdownRef = React.useRef(null);

  const currentRole = ROLES.find(r => r.id === role);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowRoleDropdown(false);
      }
    };

    if (showRoleDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showRoleDropdown]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!task.trim()) return;

    setIsLoading(true);
    
    try {
      const result = await runEmployeeAgent(role, task);
      const formattedResponse = formatEmployeeResponse(result);
      onResponse(task, formattedResponse, `employee-${role}`);
      setTask('');
    } catch (error) {
      onResponse(task, `Error: ${error.message || 'Failed to process task'}`, `employee-${role}`);
    } finally {
      setIsLoading(false);
    }
  };

  const formatEmployeeResponse = (result) => {
    let response = `## ${result.role.charAt(0).toUpperCase() + result.role.slice(1)} Response\n\n`;
    response += `**Task Type:** ${result.task_type.replace('_', ' ')}\n\n`;

    if (result.pr_draft) {
      const pr = result.pr_draft;
      response += `### PR Draft\n`;
      response += `**Title:** ${pr.title}\n`;
      response += `**Branch:** \`${pr.branch_name}\` → \`${pr.target_branch}\`\n`;
      response += `**Complexity:** ${pr.estimated_complexity}\n\n`;
      response += `**Description:**\n${pr.description}\n\n`;
      
      if (pr.files_to_modify?.length > 0) {
        response += `**Files to Modify:**\n`;
        pr.files_to_modify.forEach(f => response += `- \`${f}\`\n`);
        response += '\n';
      }
      
      if (pr.implementation_steps?.length > 0) {
        response += `**Implementation Steps:**\n`;
        pr.implementation_steps.forEach((step, i) => response += `${i + 1}. ${step}\n`);
        response += '\n';
      }

      if (pr.test_suggestions?.length > 0) {
        response += `**Test Suggestions:**\n`;
        pr.test_suggestions.forEach(t => response += `- ${t}\n`);
      }
    }

    if (result.pr_review) {
      const review = result.pr_review;
      response += `### PR Review\n`;
      response += `**Status:** ${review.approval_status.replace('_', ' ').toUpperCase()}\n\n`;
      response += `**Summary:** ${review.summary}\n\n`;

      if (review.key_concerns?.length > 0) {
        response += `**Key Concerns:**\n`;
        review.key_concerns.forEach(c => response += `- ⚠️ ${c}\n`);
        response += '\n';
      }

      if (review.positive_aspects?.length > 0) {
        response += `**Positive Aspects:**\n`;
        review.positive_aspects.forEach(p => response += `- ✓ ${p}\n`);
        response += '\n';
      }

      if (review.comments?.length > 0) {
        response += `**Review Comments:**\n`;
        review.comments.slice(0, 5).forEach(c => {
          const severity = c.severity === 'critical' ? '🔴' : c.severity === 'warning' ? '🟡' : 'ℹ️';
          response += `- ${severity} ${c.comment}\n`;
        });
      }
    }

    if (result.slack_message) {
      const msg = result.slack_message;
      response += `### Slack Message Draft\n`;
      response += `**Channel:** ${msg.channel_suggestion}\n`;
      if (msg.recipients?.length > 0) {
        response += `**Recipients:** ${msg.recipients.join(', ')}\n`;
      }
      response += `**Subject:** ${msg.subject}\n`;
      response += `**Urgency:** ${msg.urgency}\n\n`;
      response += `**Message:**\n\n${msg.message}\n`;
    }

    if (result.status_update) {
      const status = result.status_update;
      response += `### Status Update\n`;
      response += `**Summary:** ${status.summary}\n\n`;

      if (status.key_points?.length > 0) {
        response += `**Key Points:**\n`;
        status.key_points.forEach(p => response += `- ${p}\n`);
        response += '\n';
      }

      if (status.blockers?.length > 0) {
        response += `**Blockers:**\n`;
        status.blockers.forEach(b => response += `- 🚫 ${b}\n`);
        response += '\n';
      }

      if (status.next_steps?.length > 0) {
        response += `**Next Steps:**\n`;
        status.next_steps.forEach(s => response += `- → ${s}\n`);
      }
    }

    if (result.general_response) {
      response += result.general_response;
    }

    return response;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 overflow-visible" data-testid="employee-form">
      {/* Role Selector + Task Input */}
      <div className="flex gap-2 overflow-visible">
        {/* Role Dropdown */}
        <div className="relative overflow-visible" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setShowRoleDropdown(!showRoleDropdown)}
            data-testid="role-selector"
            className="h-11 px-4 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 flex items-center gap-2 transition-colors min-w-[140px]"
          >
            <currentRole.icon className="w-4 h-4 text-slate-600" />
            <span className="text-sm font-medium text-slate-700">{currentRole.label}</span>
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${showRoleDropdown ? 'rotate-180' : ''}`} />
          </button>

          {showRoleDropdown && (
            <div className="absolute bottom-full left-0 mb-1 w-48 bg-white rounded-xl border border-slate-200 shadow-lg z-50 overflow-hidden">
              {ROLES.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => {
                    setRole(r.id);
                    setShowRoleDropdown(false);
                  }}
                  data-testid={`role-option-${r.id}`}
                  className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors ${role === r.id ? 'bg-blue-50' : ''}`}
                >
                  <r.icon className={`w-5 h-5 ${role === r.id ? 'text-blue-600' : 'text-slate-500'}`} />
                  <div className="text-left">
                    <p className={`text-sm font-medium ${role === r.id ? 'text-blue-600' : 'text-slate-700'}`}>{r.label}</p>
                    <p className="text-xs text-slate-400">{r.description}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Task Input */}
        <input
          type="text"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder={`What do you need help with as ${currentRole.label.toLowerCase()}?`}
          disabled={isLoading}
          data-testid="task-input"
          className="flex-1 max-w-[60%] h-11 px-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading || !task.trim()}
          data-testid="submit-employee-btn"
          className="h-11 px-5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Working...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Submit</span>
            </>
          )}
        </button>
      </div>

      {/* Task Suggestions */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">Try:</span>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar">
          {TASK_SUGGESTIONS[role].map((suggestion, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setTask(suggestion)}
              className="px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full whitespace-nowrap transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
