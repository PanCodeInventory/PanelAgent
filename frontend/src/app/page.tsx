import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BarChart3, Bot, Brain, Search, ShieldAlert, Wrench } from "lucide-react";

export default function Home() {
  return (
    <div className="relative min-h-screen">
      <div className="absolute inset-0 bg-background pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            <span className="text-primary">PanelAgent</span>{" "}
            <span className="text-foreground">流式配色助手</span>
          </h1>
          <p className="mt-6 text-xl text-muted-foreground max-w-2xl mx-auto">
            结合确定性算法与AI评估，基于实验室真实库存生成有效的配色方案
          </p>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Brain className="h-5 w-5" />
                </div>
                <span className="text-foreground">AI 实验设计</span>
              </CardTitle>
              <CardDescription>
                让AI为您的实验推荐最佳标志物组合
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                描述您的实验目标，AI将分析您的抗体库存，推荐最优标志物组合并给出详细理由。
              </p>
              <Link href="/exp-design" className="block">
                <Button 
                  className="w-full transition-all duration-200" 
                  variant="default"
                >
                  开始实验设计
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Wrench className="h-5 w-5" />
                </div>
                <span className="text-foreground">配色方案生成</span>
              </CardTitle>
              <CardDescription>
                根据标志物列表生成无冲突的配色方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                输入您的目标标志物，让回溯求解器找到所有物理有效的配色方案，再由AI评估并选择最优方案。
              </p>
              <Link href="/panel-design" className="block">
                <Button 
                  className="w-full transition-all duration-200" 
                  variant="default"
                >
                  生成配色方案
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <ShieldAlert className="h-5 w-5" />
                </div>
                <span className="text-foreground">质量登记</span>
              </CardTitle>
              <CardDescription>报告抗体质量问题，改进配色方案</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">提交表现不佳抗体的反馈信息，供同学们进行参考，并在下一次配色生成中避免使用。</p>
              <Link href="/quality-registry" className="block">
                <Button className="w-full transition-all duration-200" variant="default">报告问题</Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="mt-20">
          <h2 className="text-3xl font-bold text-foreground text-center">
            工作原理
          </h2>
          <p className="mt-3 text-muted-foreground text-center max-w-lg mx-auto">
            搜索-评估架构，融合确定性算法与AI智能
          </p>
          
          <div className="mt-12 relative">
            <div className="hidden md:block absolute top-12 left-[16.67%] right-[16.67%] h-px bg-border" />
            
            <div className="grid gap-8 sm:grid-cols-3">
              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">01</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <Search className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
                    <h3 className="font-semibold text-card-foreground">
                      搜索阶段
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      确定性回溯算法找出所有无通道冲突的物理有效配色方案。
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">02</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <Bot className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
                    <h3 className="font-semibold text-card-foreground">
                      AI 评估
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      LLM专家根据亮度匹配和光谱重叠评估候选方案，选出最优配色。
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">03</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <BarChart3 className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
                    <h3 className="font-semibold text-card-foreground">
                      可视化
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      交互式光谱模拟和门控策略生成，助您完成最终配色选择。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
