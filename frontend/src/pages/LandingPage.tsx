import { ArrowRight, CheckCircle2, FileSearch, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import { BackendStatus } from '@/components/BackendStatus'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

const highlights = [
  {
    title: 'Structured resume parsing',
    description:
      'Upload PDF or DOCX resumes with validation, size limits, and clear parsing errors.',
    icon: FileSearch,
  },
  {
    title: 'Job-aware workflow',
    description:
      'Capture the target role and description alongside the resume to prepare for matching.',
    icon: CheckCircle2,
  },
  {
    title: 'Privacy-minded backend',
    description:
      'Resume files are processed in memory and not persisted by default during parsing.',
    icon: ShieldCheck,
  },
]

export function LandingPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-16">
      <section className="grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-500">
          <p className="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200">
            Resume intelligence for modern hiring workflows
          </p>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
              Align your resume with the roles you want
            </h1>
            <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
              ResumeFit AI helps you compare resume content against job
              descriptions, surface skill gaps, and build improvement plans.
              Run a full analysis from the Analyze page after uploading your resume
              and job description.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button asChild size="lg" className="shadow-md shadow-indigo-500/20">
              <Link to="/analyze">
                Start resume analysis
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="#how-it-works">See how it works</a>
            </Button>
          </div>
        </div>

        <div className="animate-in fade-in slide-in-from-right-2 duration-500">
          <BackendStatus />
        </div>
      </section>

      <section id="how-it-works" className="mt-16 space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            Built for a clean analysis workflow
          </h2>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Upload and parse resumes, run deterministic alignment scoring, and
            optionally request consent-based AI recommendations—without fabricated
            results.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {highlights.map(({ title, description, icon: Icon }) => (
            <Card
              key={title}
              className="transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <CardHeader>
                <div className="mb-2 inline-flex size-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/15 to-violet-500/20 text-indigo-600">
                  <Icon className="size-5" aria-hidden="true" />
                </div>
                <CardTitle className="text-base">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          ))}
        </div>
      </section>
    </main>
  )
}
