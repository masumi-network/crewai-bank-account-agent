from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from crew_definition import BankingAnalysisCrew

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Banking Analysis API",
    description="AI-powered banking transaction analysis and reporting",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

class BankConfig(BaseModel):
    api_key: str
    api_url: str

class AnalysisRequest(BaseModel):
    date_range: DateRange
    bank_configs: Dict[str, BankConfig]
    output_formats: Optional[List[str]] = ["json", "pdf"]

# Initialize banking configuration
def get_bank_configs() -> Dict[str, Dict[str, str]]:
    return {
        'wise': {
            'api_key': os.getenv('WISE_API_KEY'),
            'api_url': os.getenv('WISE_API_URL', 'https://api.wise.com/v1')
        },
        'revolut': {
            'api_key': os.getenv('REVOLUT_API_KEY'),
            'api_url': os.getenv('REVOLUT_API_URL', 'https://api.revolut.com/business/latest')
        },
        'google_sheets_credentials': os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    }

# API endpoints
@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "1.0.0",
        "supported_banks": ["wise", "revolut"]
    }

@app.post("/analyze")
async def analyze_transactions(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Analyze banking transactions and generate reports
    """
    try:
        # Initialize crew with bank configurations
        bank_configs = {
            bank: {
                'api_key': config.api_key,
                'api_url': config.api_url
            }
            for bank, config in request.bank_configs.items()
        }
        
        crew = BankingAnalysisCrew(
            config=bank_configs,
            verbose=True
        )
        
        # Run analysis
        results = await crew.run(
            date_range=request.date_range.dict()
        )
        
        return {
            "status": "success",
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 