import { Header } from '@/components/common/Header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Activity, Droplets, Pill } from 'lucide-react';

const scenarios = [
  {
    id: 'cbc',
    title: 'CBC Blood Test Results',
    icon: Droplets,
    description: 'Patient receives a complete blood count with values for white blood cells, red blood cells, and other markers. One or two values fall outside the normal range.',
    tests: 'Can patients read numbers, understand normal ranges, and interpret what abnormal values mean for their health.',
    clinical: {
      static: 'The Explainer presents lab results in a structured clinical format using medical terminology (e.g., "hemoglobin," "leukocytes," "reference interval") — similar to how a lab report would appear. No follow-up interaction.',
      dialog: 'The Explainer presents results using medical language, then engages in conversation. Adjusts explanations based on patient questions but maintains clinical framing.',
    },
    analogy: {
      static: 'The Explainer uses everyday language and analogies — red blood cells as "oxygen delivery trucks," white blood cells as "infection fighters." Explains what high or low numbers mean in plain terms. No follow-up.',
      dialog: 'The Explainer uses plain language and analogies, then has a back-and-forth conversation. Adapts explanations, adds new analogies, and checks comprehension along the way.',
    },
    quizTopics: ['Identify which values are abnormal', 'Explain what hemoglobin does', 'Describe what a high WBC count might indicate', 'Interpret "normal range"'],
  },
  {
    id: 'prediabetes',
    title: 'Pre-Diabetes Diagnosis',
    icon: Activity,
    description: 'Patient learns they have pre-diabetes based on their HbA1c number. Must understand the condition and a management plan involving lifestyle changes.',
    tests: 'Can patients understand a chronic condition, grasp what HbA1c represents, and translate medical advice into actionable daily changes.',
    clinical: {
      static: 'The Explainer provides textbook diagnostic criteria (HbA1c 5.7–6.4%), clinical treatment guidelines, and standard medical recommendations. Formal tone, structured format.',
      dialog: 'Clinical language with interactive follow-up. The Explainer answers questions about criteria and guidelines while maintaining medical framing.',
    },
    analogy: {
      static: 'Blood sugar explained as a thermostat that should stay in a certain range. HbA1c described as a "three-month report card for blood sugar." Lifestyle changes framed as specific daily actions rather than vague medical advice.',
      dialog: 'Analogy-based explanation with conversation. The Explainer checks understanding, introduces new metaphors when needed, and helps the patient connect concepts to their daily life.',
    },
    quizTopics: ['What HbA1c measures', 'What the patient\'s number means', 'Name two lifestyle changes', 'When to follow up with doctor'],
  },
  {
    id: 'medication',
    title: 'Medication Instructions',
    icon: Pill,
    description: 'Patient receives a prescription with complex dosing rules — start at one dose, increase after two weeks if symptoms persist, and watch for side effects requiring a doctor call.',
    tests: 'Can patients turn an explanation into the correct action — proper dosing schedule, when to adjust, and when to seek help.',
    clinical: {
      static: 'Pharmacy-style language with standard dosing notation, contraindications, and adverse event warnings. Structured like a medication information sheet.',
      dialog: 'Clinical medication counseling with Q&A. The Explainer addresses patient concerns about side effects and dosing using professional terminology.',
    },
    analogy: {
      static: 'Step-by-step walkthrough in plain English. "Take one pill each morning with breakfast for the first two weeks. If you still feel X after two weeks, switch to two pills." Side effects described in everyday terms.',
      dialog: 'Plain-language walkthrough with conversation. The Explainer walks through each step, confirms understanding, and uses concrete daily-life examples to anchor the instructions.',
    },
    quizTopics: ['Starting dose and schedule', 'When to increase dosage', 'Side effects requiring doctor call', 'What to do if a dose is missed'],
  },
];

export function ScenariosPage() {
  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Scenarios">
        <Badge variant="secondary">{scenarios.length} scenarios</Badge>
      </Header>
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col gap-6 p-6">
          <p className="text-sm text-muted-foreground max-w-2xl">
            Three medical scenarios designed to test different aspects of health comprehension. Each scenario has four explanation variants from the 2×2 design (clinical/analogy × static/dialog).
          </p>

          {scenarios.map((scenario) => {
            const Icon = scenario.icon;
            return (
              <Card key={scenario.id}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle>{scenario.title}</CardTitle>
                      <CardDescription>{scenario.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">What this tests</p>
                    <p className="text-sm">{scenario.tests}</p>
                  </div>

                  <Separator className="mb-4" />

                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3">Explanation Variants</p>
                  <Tabs defaultValue={0}>
                    <TabsList>
                      <TabsTrigger value={0}>Clinical + Static</TabsTrigger>
                      <TabsTrigger value={1}>Clinical + Dialog</TabsTrigger>
                      <TabsTrigger value={2}>Analogy + Static</TabsTrigger>
                      <TabsTrigger value={3}>Analogy + Dialog</TabsTrigger>
                    </TabsList>
                    <TabsContent value={0}>
                      <div className="mt-3 rounded-md bg-muted/50 p-4 text-sm">{scenario.clinical.static}</div>
                    </TabsContent>
                    <TabsContent value={1}>
                      <div className="mt-3 rounded-md bg-muted/50 p-4 text-sm">{scenario.clinical.dialog}</div>
                    </TabsContent>
                    <TabsContent value={2}>
                      <div className="mt-3 rounded-md bg-muted/50 p-4 text-sm">{scenario.analogy.static}</div>
                    </TabsContent>
                    <TabsContent value={3}>
                      <div className="mt-3 rounded-md bg-muted/50 p-4 text-sm">{scenario.analogy.dialog}</div>
                    </TabsContent>
                  </Tabs>

                  <Separator className="my-4" />

                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">Comprehension Quiz Topics</p>
                  <ul className="grid grid-cols-2 gap-1">
                    {scenario.quizTopics.map((topic) => (
                      <li key={topic} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/40" />
                        {topic}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
