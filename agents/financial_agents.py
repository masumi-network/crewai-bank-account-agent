"""
CrewAI agents for financial analysis.
"""
from crewai import Agent, Task, Crew, Process
from typing import Dict, List, Any, Optional
import pandas as pd
import logging
import os
import traceback
import openai
import json
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class FinancialAgents:
    """
    Financial analysis agents using CrewAI.
    """
    
    def __init__(self, accounts_data: pd.DataFrame, transactions_data: pd.DataFrame, summary_stats: Dict, openai_api_key: Optional[str] = None):
        """
        Initialize the financial agents.
        
        Args:
            accounts_data: DataFrame with account data
            transactions_data: DataFrame with transaction data
            summary_stats: Dictionary with summary statistics
            openai_api_key: OpenAI API key for CrewAI agents
        """
        self.accounts_data = accounts_data
        self.transactions_data = transactions_data
        self.summary_stats = summary_stats
        self.openai_api_key = openai_api_key
        
        # Set OpenAI API key as environment variable if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            # Also set it directly in the openai module
            openai.api_key = openai_api_key
            
            # Log that we've set the API key
            logger.info("OpenAI API key has been set")
            
            # Test the OpenAI API key
            try:
                # Simple test call to OpenAI
                llm = ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature=0.7,
                    openai_api_key=openai_api_key
                )
                response = llm.invoke("Test")
                logger.info("OpenAI API key is valid")
            except Exception as e:
                logger.error(f"Error testing OpenAI API key: {str(e)}")
                logger.error(traceback.format_exc())
                raise ValueError(f"Invalid OpenAI API key: {str(e)}")
    
    def create_agents(self):
        """
        Create the financial analysis agents.
        
        Returns:
            Tuple of (data_analyst, financial_advisor, budget_optimizer) agents
        """
        # Create a language model
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # Data Analyst Agent
        data_analyst = Agent(
            role="Financial Data Analyst",
            goal="Analyze financial transaction data to identify patterns and trends",
            backstory="""You are an expert financial data analyst with years of experience in 
            analyzing personal and business financial data. You have a keen eye for patterns 
            and can extract valuable insights from transaction data.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
        
        # Financial Advisor Agent
        financial_advisor = Agent(
            role="Financial Advisor",
            goal="Provide personalized financial advice based on transaction data",
            backstory="""You are a certified financial advisor with expertise in personal finance, 
            investment strategies, and financial planning. You help clients make informed decisions 
            about their money and achieve their financial goals.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
        
        # Budget Optimizer Agent
        budget_optimizer = Agent(
            role="Budget Optimizer",
            goal="Identify opportunities to optimize spending and increase savings",
            backstory="""You are a budget optimization specialist who helps individuals and 
            businesses reduce unnecessary expenses and maximize savings. You have a talent for 
            finding inefficiencies in spending patterns and suggesting practical alternatives.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
        
        return data_analyst, financial_advisor, budget_optimizer
    
    def create_tasks(self, data_analyst, financial_advisor, budget_optimizer):
        """
        Create tasks for the financial analysis agents.
        
        Args:
            data_analyst: The data analyst agent
            financial_advisor: The financial advisor agent
            budget_optimizer: The budget optimizer agent
            
        Returns:
            List of tasks
        """
        # Convert DataFrames to JSON strings for the agents to use
        # Use all available data
        accounts_json = self.accounts_data.to_json(orient='records')
        transactions_json = self.transactions_data.to_json(orient='records')
        summary_json = json.dumps(self.summary_stats)
        
        # Create a data analysis task
        analysis_task = Task(
            description=f"""
            Analyze the financial transaction data and identify key patterns and trends.
            
            Focus on:
            1. Income and expense patterns
            2. Spending categories analysis
            3. Cash flow trends
            4. Unusual transactions or anomalies
            5. Account balance analysis
            
            Here is the complete account data with balances:
            {accounts_json}
            
            Here is the complete transaction data:
            {transactions_json}
            
            Here are the summary statistics:
            {summary_json}
            
            Provide a comprehensive analysis with specific insights.
            Your output should start with "# Data Analysis" as a header.
            Make sure to include analysis of the account balances and how they've changed over time.
            """,
            agent=data_analyst,
            expected_output="A detailed analysis of the financial data with key insights and patterns."
        )
        
        # Create a financial advice task
        advice_task = Task(
            description=f"""
            Based on the financial data and the analysis from the Data Analyst, provide personalized financial advice.
            
            Focus on:
            1. Savings recommendations based on current account balances
            2. Spending habit improvements
            3. Financial goal planning
            4. Risk management
            5. Currency management (if multiple currencies are used)
            
            Here is the complete account data with balances:
            {accounts_json}
            
            Here is the complete transaction data:
            {transactions_json}
            
            Here are the summary statistics:
            {summary_json}
            
            Provide specific, actionable advice tailored to this financial situation.
            Your output should start with "# Financial Advice" as a header.
            Include at least 5 specific recommendations that the user can implement immediately.
            Make sure to reference the actual account balances and transaction patterns in your advice.
            """,
            agent=financial_advisor,
            expected_output="Personalized financial advice with specific recommendations."
        )
        
        # Create a budget optimization task
        optimization_task = Task(
            description=f"""
            Identify opportunities to optimize the budget and reduce unnecessary expenses.
            
            Focus on:
            1. Identifying recurring expenses that could be reduced
            2. Suggesting alternatives for high-cost services
            3. Highlighting potential savings opportunities
            4. Proposing a realistic budget plan based on actual income and expenses
            5. Optimizing use of different currency accounts (if applicable)
            
            Here is the complete account data with balances:
            {accounts_json}
            
            Here is the complete transaction data:
            {transactions_json}
            
            Here are the summary statistics:
            {summary_json}
            
            Provide specific, actionable recommendations for budget optimization.
            Your output should start with "# Budget Optimization" as a header.
            Include at least 5 specific areas where the user can save money, with estimated savings amounts.
            Base your recommendations on the actual transaction history and account balances.
            """,
            agent=budget_optimizer,
            expected_output="A detailed budget optimization plan with specific recommendations for reducing expenses."
        )
        
        return [analysis_task, advice_task, optimization_task]
    
    def run_analysis(self):
        """
        Run the financial analysis using CrewAI.
        
        Returns:
            Dictionary with the analysis results
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for AI analysis")
        
        try:
            logger.info("Starting financial analysis")
            
            # Check if OpenAI API key is set
            if not os.environ.get("OPENAI_API_KEY"):
                logger.error("OpenAI API key is not set")
                return {
                    "analysis": "Error during analysis: OpenAI API key is not set. Please provide a valid OpenAI API key.",
                    "advice": "",
                    "optimization": "",
                    "recommendations": []
                }
            
            # Create agents
            data_analyst, financial_advisor, budget_optimizer = self.create_agents()
            
            # Create tasks
            tasks = self.create_tasks(data_analyst, financial_advisor, budget_optimizer)
            
            # Create a crew with the agents and tasks
            crew = Crew(
                agents=[data_analyst, financial_advisor, budget_optimizer],
                tasks=tasks,
                verbose=True,
                process=Process.sequential
            )
            
            # Run the crew
            logger.info("Running CrewAI analysis")
            result = crew.kickoff()
            logger.info("Crew analysis complete")
            
            # Process results
            logger.info("Processing results...")
            
            try:
                # Extract results from the crew's output
                # In newer versions of CrewAI, the result is a CrewOutput object with task_output attribute
                analysis_results = ""
                advice_results = ""
                optimization_results = ""
                
                # Log the type and structure of the result for debugging
                logger.info(f"Result type: {type(result)}")
                logger.info(f"Result attributes: {dir(result)}")
                
                # Check if the result has tasks attribute (newer CrewAI versions)
                if hasattr(result, 'tasks'):
                    logger.info(f"Found tasks attribute with {len(result.tasks)} tasks")
                    for i, task_result in enumerate(result.tasks):
                        logger.info(f"Processing task {i+1}")
                        task_description = task_result.description.lower() if hasattr(task_result, 'description') else ""
                        task_output = task_result.output if hasattr(task_result, 'output') else ""
                        
                        if "analyze the financial transaction data" in task_description:
                            analysis_results = task_output
                        elif "provide personalized financial advice" in task_description:
                            advice_results = task_output
                        elif "optimize the budget" in task_description:
                            optimization_results = task_output
                
                # If we still don't have results, use the string representation of the result
                if not analysis_results:
                    logger.info("Using string representation of result")
                    result_str = str(result)
                    
                    # Try to extract sections based on headers
                    if "# Data Analysis" in result_str:
                        parts = result_str.split("# Data Analysis")
                        if len(parts) > 1:
                            analysis_part = parts[1]
                            if "# Financial Advice" in analysis_part:
                                analysis_results = analysis_part.split("# Financial Advice")[0].strip()
                                advice_part = analysis_part.split("# Financial Advice")[1]
                                if "# Budget Optimization" in advice_part:
                                    advice_results = advice_part.split("# Budget Optimization")[0].strip()
                                    optimization_results = advice_part.split("# Budget Optimization")[1].strip()
                                else:
                                    advice_results = advice_part.strip()
                            else:
                                analysis_results = analysis_part.strip()
                    else:
                        # Just use the whole output as analysis
                        analysis_results = result_str
                
                # If we still don't have advice or optimization results, create default ones
                if not advice_results:
                    advice_results = """
                    # Financial Advice
                    
                    Based on the financial data analysis, here are some general recommendations:
                    
                    1. Create a budget to track your income and expenses
                    2. Build an emergency fund of 3-6 months of expenses
                    3. Reduce spending in your highest expense categories
                    4. Consider automating savings with regular transfers
                    5. Review and cancel unused subscriptions
                    """
                
                if not optimization_results:
                    optimization_results = """
                    # Budget Optimization
                    
                    Here are some general budget optimization suggestions:
                    
                    1. Review your entertainment expenses and consider reducing them
                    2. Look for cheaper alternatives for food and dining
                    3. Consider using public transportation more often
                    4. Bundle services where possible to get discounts
                    5. Negotiate bills and subscriptions for better rates
                    """
                
                # Extract recommendations
                recommendations = self._extract_recommendations(advice_results, optimization_results)
                
                return {
                    "analysis": analysis_results,
                    "advice": advice_results,
                    "optimization": optimization_results,
                    "recommendations": recommendations
                }
            
            except Exception as e:
                logger.error(f"Error processing results: {e}", exc_info=True)
                error_message = f"Error processing results: {str(e)}\n\n"
                error_message += traceback.format_exc()
                
                return {
                    "analysis": error_message,
                    "advice": "",
                    "optimization": "",
                    "recommendations": []
                }
        except Exception as e:
            logger.error(f"Error in run_analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a meaningful error message
            return {
                "analysis": f"Error during analysis: {str(e)}",
                "advice": "Unable to generate advice due to an error.",
                "optimization": "Unable to generate optimization plan due to an error.",
                "recommendations": [
                    "Please check your OpenAI API key and try again.",
                    "Ensure you have sufficient credits in your OpenAI account.",
                    "Try refreshing the page and regenerating the analysis."
                ]
            }
    
    def _extract_recommendations(self, advice: str, optimization: str) -> List[str]:
        """
        Extract recommendations from the advice and optimization results.
        
        Args:
            advice: Financial advice text
            optimization: Budget optimization text
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Try to extract recommendations from the text
        try:
            # Look for numbered lists, bullet points, or sections labeled "recommendations"
            lines = (advice + "\n" + optimization).split("\n")
            
            for line in lines:
                line = line.strip()
                
                # Check for numbered recommendations
                if (line.startswith("1.") or line.startswith("1)") or 
                    line.startswith("•") or line.startswith("*") or
                    line.startswith("-")):
                    recommendations.append(line.lstrip("1.)•*- ").strip())
                
                # Check for lines containing key recommendation phrases
                elif ("recommend" in line.lower() or 
                      "should" in line.lower() or 
                      "could" in line.lower() or
                      "consider" in line.lower()):
                    recommendations.append(line)
            
            # Limit to top 10 recommendations
            recommendations = recommendations[:10]
            
            # If no recommendations were found, provide default ones
            if not recommendations:
                recommendations = [
                    "Review your spending patterns to identify areas for potential savings.",
                    "Consider setting up automatic transfers to a savings account.",
                    "Track your expenses more closely to better understand your financial habits."
                ]
        
        except Exception as e:
            logger.error(f"Error extracting recommendations: {e}", exc_info=True)
            recommendations = [
                "Review your spending patterns to identify areas for potential savings.",
                "Consider setting up automatic transfers to a savings account.",
                "Track your expenses more closely to better understand your financial habits."
            ]
        
        return recommendations 