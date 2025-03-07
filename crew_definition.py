from crewai import Agent, Crew, Task
from typing import Dict
from banking_tools import BankingTools

class BankingAnalysisCrew:
    """CrewAI implementation for banking analysis"""
    
    def __init__(self, config: Dict[str, Dict[str, str]], verbose=True):
        self.verbose = verbose
        self.banking_tools = BankingTools(config)
        self.agents = self.create_agents()
        self.crew = self.create_crew()

    def create_agents(self):
        # Data Analysis Agent
        data_analyst = Agent(
            role='Financial Data Analyst',
            goal='Analyze banking transactions and identify patterns',
            backstory="""Expert financial analyst specializing in transaction analysis,
            pattern recognition, and cost optimization. You excel at identifying 
            opportunities for financial improvement and providing actionable insights.""",
            verbose=self.verbose,
            allow_delegation=True
        )

        # Report Generation Agent
        report_generator = Agent(
            role='Financial Report Specialist',
            goal='Create comprehensive financial reports and visualizations',
            backstory="""Specialist in creating clear, actionable financial reports
            and visualizations. You excel at presenting complex financial data in an
            understandable format and generating insights that drive decision-making.""",
            verbose=self.verbose,
            allow_delegation=False
        )

        return {
            'data_analyst': data_analyst,
            'report_generator': report_generator
        }

    def create_crew(self):
        agents = self.agents

        tasks = [
            Task(
                description="""Analyze banking transactions to identify patterns,
                categorize spending, and find cost-saving opportunities. Focus on:
                1. Transaction categorization
                2. Spending patterns
                3. Recurring payments
                4. Cost optimization opportunities""",
                agent=agents['data_analyst']
            ),
            Task(
                description="""Generate comprehensive financial reports based on the
                analysis. Include:
                1. Executive summary
                2. Detailed transaction analysis
                3. Cost-saving recommendations
                4. Visual representations of key metrics""",
                agent=agents['report_generator']
            )
        ]

        return Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=self.verbose
        )

    async def run(self, date_range: Dict) -> Dict:
        """
        Execute the banking analysis workflow
        
        Args:
            date_range (dict): Start and end dates for analysis
            
        Returns:
            dict: Analysis results and reports
        """
        try:
            # Fetch transactions from all configured banks
            all_transactions = []
            for bank_type in self.banking_tools.banks:
                transactions = await self.banking_tools.get_transactions(
                    bank_type=bank_type,
                    start_date=date_range['start_date'],
                    end_date=date_range['end_date']
                )
                all_transactions.extend(transactions)
            
            # Analyze transactions
            analysis_results = await self.banking_tools.analyze_costs(all_transactions)
            
            # Generate reports
            reports = await self.banking_tools.generate_report(
                analysis_results,
                output_formats=['json', 'pdf', 'sheets']
            )
            
            # Combine results
            return {
                'analysis': analysis_results,
                'reports': reports,
                'transaction_count': len(all_transactions)
            }
        finally:
            await self.banking_tools.close()