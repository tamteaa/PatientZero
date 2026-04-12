import { useEffect, useState } from 'react';
import { useAtomValue } from 'jotai';
import { getPatientDistribution } from '@/api/sessions';
import { experimentsAtom } from '@/atoms/experiment';
import { PatientDistributionCard } from '../distributions/PatientDistributionCard';
import { DoctorDistributionCard } from '../distributions/DoctorDistributionCard';

interface Props {
  experimentId: string;
}

export function DistributionsTab({ experimentId }: Props) {
  const experiments = useAtomValue(experimentsAtom);
  const experiment = experiments.find((e) => e.id === experimentId) ?? null;
  const [ageRanges, setAgeRanges] = useState<Record<string, [number, number]>>({});

  useEffect(() => {
    getPatientDistribution()
      .then((r) => setAgeRanges(r.age_bucket_ranges))
      .catch(() => {});
  }, []);

  if (!experiment) {
    return <p className="text-xs text-muted-foreground">Loading distributions…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold">Target distributions</h3>
        <p className="text-xs text-muted-foreground">
          Profiles for simulations in this experiment are sampled from these tables.
        </p>
      </div>
      <PatientDistributionCard dist={experiment.patient_distribution} ageRanges={ageRanges} />
      <DoctorDistributionCard dist={experiment.doctor_distribution} />
    </div>
  );
}
