import React from 'react';
import { GraduationCap, Monitor, BarChart3 } from 'lucide-react';

export default function Brand({compact=false}) {
  return <div className={`brand-identity ${compact ? 'compact' : ''}`}>
    <div className="brand-emblem"><GraduationCap className="brand-cap" size={34} strokeWidth={2.7}/><Monitor className="brand-monitor" size={40} strokeWidth={2.4}/><BarChart3 className="brand-chart" size={22} strokeWidth={3}/></div>
    <div className="brand-words"><strong>EDU-<span>INFRA</span></strong><small>ANALYTICS 1.6</small></div>
  </div>;
}
