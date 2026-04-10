import { useEffect } from 'react';
import { useAtom } from 'jotai';
import { Header } from '@/components/common/Header';
import { Card, CardContent } from '@/components/ui/card';
import { getSettings } from '@/api/sessions';
import { appSettingsAtom } from '@/atoms/model';

export function SettingsPage() {
  const [settings, setSettings] = useAtom(appSettingsAtom);

  useEffect(() => {
    if (!settings) getSettings().then(setSettings).catch(() => {});
  }, []);

  return (
    <>
      <Header title="Settings" />
      <div className="flex-1 p-6 max-w-2xl">
        <Card>
          <CardContent className="py-4 space-y-3">
            {settings ? (
              <div className="flex items-center justify-between text-sm">
                <div className="flex flex-col">
                  <span className="font-medium">Max concurrent simulations</span>
                  <span className="text-xs text-muted-foreground">
                    Hard cap on parallel simulation runs. Requests beyond this return 429.
                  </span>
                </div>
                <span className="tabular-nums text-base font-semibold">
                  {settings.max_concurrent_simulations}
                </span>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading…</div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
