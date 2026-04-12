import { useEffect, useRef, useState } from 'react';
import { useSetAtom } from 'jotai';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { createExperiment, listExperiments } from '@/api/sessions';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';

export function NewExperimentDialog() {
  const { handleError } = useError();
  const setExperiments = useSetAtom(experimentsAtom);
  const setActiveExperimentId = useSetAtom(activeExperimentIdAtom);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName('');
      // focus the input on open
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const handleCreate = async () => {
    const trimmed = name.trim();
    if (!trimmed || creating) return;
    setCreating(true);
    try {
      const exp = await createExperiment(trimmed);
      setExperiments(await listExperiments());
      setActiveExperimentId(exp.id);
      setOpen(false);
    } catch (err) {
      handleError(err, 'Failed to create experiment');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button
        variant="outline"
        size="sm"
        className="w-full h-7 gap-1.5 text-xs justify-start"
        onClick={() => setOpen(true)}
      >
        <Plus className="h-3.5 w-3.5" /> New experiment
      </Button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New experiment</DialogTitle>
          <DialogDescription>
            Give it a name. You can rename, configure, and optimize it after it's created.
          </DialogDescription>
        </DialogHeader>
        <Input
          ref={inputRef}
          placeholder="e.g. CBC low-literacy pilot"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleCreate();
            if (e.key === 'Escape') setOpen(false);
          }}
          className="h-9 text-sm"
        />
        <DialogFooter>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={() => setOpen(false)}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            size="sm"
            className="h-8 text-xs"
            onClick={handleCreate}
            disabled={creating || !name.trim()}
          >
            {creating ? 'Creating…' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
