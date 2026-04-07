import { ScrollArea } from '@/components/ui/scroll-area';
import { NavItem } from './NavItem';
import {
  Play,
  LayoutDashboard,
  MessageSquare,
  Scale,
  BarChart2,
} from 'lucide-react';

export function AppSidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-muted/30">
      <div className="flex h-12 items-center border-b border-border px-4">
        <span className="text-sm font-bold">PatientZero</span>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-3">
          <NavItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavItem to="/simulations" icon={Play} label="Simulations" />
          <NavItem to="/chat" icon={MessageSquare} label="Chat" />
          <NavItem to="/judge" icon={Scale} label="Judge" />
          <NavItem to="/analysis" icon={BarChart2} label="Analysis" />
        </div>
      </ScrollArea>
    </div>
  );
}
