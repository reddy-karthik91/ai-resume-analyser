import os
import unittest
from app.schemas.analysis.prompt_request import PromptRequest
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.services.gemini_service import GeminiService
from app.exceptions.api_exceptions import APIException

class TestGeminiIntegration(unittest.TestCase):
    """Manual integration test verifying live Gemini API completion calls."""

    def test_live_generate(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.skipTest("Skipping integration test: GEMINI_API_KEY environment variable not set.")
            
        service = GeminiService(
            api_key=api_key,
            default_model="gemini-2.0-flash",
            timeout_seconds=30
        )
        
        request = PromptRequest(
            system_prompt="You are a helpful assistant. Always output a valid JSON containing key 'greeting'.",
            user_prompt="Say hello in JSON",
            model="gemini-2.0-flash",
            temperature=0.7,
            max_output_tokens=100,
            top_p=0.9,
            prompt_version="v1"
        )
        try:
            response = service.generate(request)
        except APIException as e:
            if e.status_code == 429:
                self.skipTest(f"Skipping integration test: Gemini API quota exceeded: {e}")
            raise
        
        # Core checks
        self.assertIsInstance(response, PromptResponse)
        self.assertEqual(response.model_used, "gemini-2.0-flash")
        self.assertEqual(response.finish_reason, FinishReason.STOP)
        self.assertIn("greeting", response.content)
        self.assertIsNotNone(response.token_usage)
        self.assertTrue(response.token_usage.total_tokens > 0)  # type: ignore
        self.assertTrue(response.response_time_ms > 0)

    def test_live_pipeline_flow(self):
        """Verify the full pipeline: Upload -> Parse PDF -> Build Prompt -> Gemini -> Format Result."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.skipTest("Skipping integration test: GEMINI_API_KEY environment variable not set.")
            
        
        os.environ["LLM_PROVIDER"] = "gemini"
        from app import create_app
        app = create_app("testing")
        app.config["GEMINI_API_KEY"] = api_key
        
        with app.app_context():
            pipeline = app.extensions["resume_pipeline"]
            
            # 1. Create a dummy upload file
            import io
            from werkzeug.datastructures import FileStorage
            dummy_file = io.BytesIO(b"%PDF-1.4\n%\\xE2\\xE3\\xCF\\xD3\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources << >>\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<< /Length 51 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Senior Python Backend Developer with 5 years Flask experience) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000015 00000 n \n0000000074 00000 n \n0000000134 00000 n \n0000000224 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n326\n%%EOF")
            
            dummy_storage = FileStorage(
                stream=dummy_file,
                filename="integration_test_resume.pdf",
                content_type="application/pdf"
            )
            
            # Upload
            upload_meta = pipeline.upload_resume(dummy_storage)
            doc_id = upload_meta.uploadId
            
            try:
                # 2. Execute full analyze flow
                result = pipeline.analyze_resume(doc_id)
                
                # Asserts
                self.assertEqual(result.document_id, doc_id)
                self.assertTrue(result.analysis_successful)
                self.assertTrue(0.0 <= result.overall_score <= 100.0)
                self.assertTrue(len(result.recommendations) > 0)
                self.assertEqual(result.analysis_metadata.provider, "Google Gemini")
            except APIException as e:
                if e.status_code == 429:
                    self.skipTest(f"Skipping integration test: Gemini API quota exceeded: {e}")
                raise
            finally:
                # Clean up stored file
                upload_dir = app.config.get("UPLOAD_FOLDER")
                stored_path = os.path.join(upload_dir, upload_meta.storedFilename)
                if os.path.exists(stored_path):
                    os.remove(stored_path)
