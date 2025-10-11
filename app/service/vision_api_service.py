import json, os, io
import asyncio
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core import retry as gretry
from typing import Dict, Any, List, Optional

class VisionApiService:
    def __init__(self):
        # ADC（Application Default Credentials）フォールバック対応
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        # クライアント初期化（ADCフォールバック対応）
        if self.credentials_path and os.path.exists(self.credentials_path):
            # Service Account認証
            self.credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
            self.client = vision.ImageAnnotatorClient(credentials=self.credentials)
        else:
            # ADC（Cloud Run等で自動認証）
            self.client = vision.ImageAnnotatorClient()
        
        # スレッドプールエグゼキューター（同期APIを非同期で実行するため）
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """ Vision APIで画像を分析する関数（非同期対応） """
        
        try:
            # 画像ファイルを読み込む
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Vision APIの画像オブジェクトを作成
            image = vision.Image(content=content)

            # 1回のAPI呼び出しで複数の解析を実行（効率化）
            loop = asyncio.get_running_loop()  # 3.12対応
            response = await loop.run_in_executor(
                self.executor, 
                self._analyze_image_sync, 
                image
            )
            
            # 結果を整理
            analysis_result = self._parse_response(response)
            
            return analysis_result
        
        except Exception as e:
            # エラーが発生した場合は基本的な情報のみ返す
            return {
                "error": f"Vision API解析に失敗しました: {str(e)}",
                "labels": [],
                "text": [],
                "objects": [],
                "faces": [],
                "safe_search": {},
                "colors": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _analyze_image_sync(self, image: vision.Image) -> vision.AnnotateImageResponse:
        """同期版の画像解析（スレッドプールで実行）"""
        # 言語ヒント付きのImageContext（日本語OCR安定化）
        image_context = vision.ImageContext(
            language_hints=['ja', 'en']
        )
        
        # 1回のAPI呼び出しで複数の解析を実行
        features = [
            vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION),
            vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.FACE_DETECTION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
            vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES)  # 色情報取得
        ]
        
        request = vision.AnnotateImageRequest(
            image=image, 
            features=features,
            image_context=image_context
        )
        
        # タイムアウト＆リトライ設定（修正版）
        return self.client.annotate_image(
            request=request,
            retry=gretry.Retry(deadline=30.0)  # リトライのみ設定
        )
    
    def _parse_response(self, response: vision.AnnotateImageResponse) -> Dict[str, Any]:
        """APIレスポンスを解析して構造化データに変換"""
        
        # 空レスポンスのガード
        if response is None:
            return {
                "error": "Empty response from Vision API",
                "labels": [],
                "text": [],
                "objects": [],
                "faces": [],
                "safe_search": {},
                "colors": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # エラーハンドリング（部分失敗も含む）
        if response.error.message:
            return {
                "error": f"Vision API解析エラー: {response.error.message}",
                "labels": [],
                "text": [],
                "objects": [],
                "faces": [],
                "safe_search": {},
                "colors": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        analysis_result = {
            "labels": self._extract_labels(response.label_annotations)[:10],  # 軽量化ガード
            "text": self._extract_text(response.text_annotations, response.full_text_annotation)[:20],
            "objects": self._extract_objects(response.localized_object_annotations)[:20],
            "faces": self._extract_faces(response.face_annotations)[:10],
            "safe_search": self._extract_safe_search(response.safe_search_annotation),
            "colors": self._extract_colors(response.image_properties_annotation),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return analysis_result
    
    def _extract_labels(self, label_annotations: List) -> List[Dict[str, Any]]:
        """ラベル検出結果を抽出"""
        labels = []
        if label_annotations:
            for label in label_annotations:
                labels.append({
                    "description": label.description,
                    "confidence": label.score,
                    "mid": label.mid
                })
        return labels
    
    def _extract_text(self, text_annotations: List, full_text_annotation) -> List[Dict[str, Any]]:
        """テキスト検出結果を抽出（DOCUMENT_TEXT_DETECTION対応）"""
        text_results = []
        
        # full_text_annotation.text（手書き・日本語に強い）
        if full_text_annotation and getattr(full_text_annotation, "text", None):
            text_results.append({
                "description": full_text_annotation.text,
                "confidence": 1.0,
                "type": "full_text",
                "bounding_poly": {"vertices": [], "coordinate_system": "normalized"}  # bboxは省略でOK
            })
        
        # 個別のテキストアノテーション
        if text_annotations:
            for text in text_annotations:
                text_results.append({
                    "description": text.description,
                    "confidence": getattr(text, 'score', 1.0),
                    "type": "individual_text",
                    "bounding_poly": self._extract_bounding_poly(text.bounding_poly, normalized=True)
                })
        
        return text_results
    
    def _extract_objects(self, object_annotations: List) -> List[Dict[str, Any]]:
        """オブジェクト検出結果を抽出（normalized_vertices対応）"""
        objects = []
        if object_annotations:
            for obj in object_annotations:
                objects.append({
                    "name": obj.name,
                    "confidence": obj.score,
                    "mid": obj.mid,
                    "bounding_poly": self._extract_normalized_vertices(obj.bounding_poly)
                })
        return objects
    
    def _extract_faces(self, face_annotations: List) -> List[Dict[str, Any]]:
        """顔検出結果を抽出（ピクセル座標固定）"""
        faces = []
        if face_annotations:
            for face in face_annotations:
                faces.append({
                    "joy_likelihood": face.joy_likelihood.name,
                    "sorrow_likelihood": face.sorrow_likelihood.name,
                    "anger_likelihood": face.anger_likelihood.name,
                    "surprise_likelihood": face.surprise_likelihood.name,
                    "bounding_poly": self._extract_bounding_poly(face.bounding_poly, normalized=False)  # ピクセル座標固定
                })
        return faces
    
    def _extract_safe_search(self, safe_search_annotation) -> Dict[str, str]:
        """安全検索結果を抽出（spoof/spoofed両対応）"""
        if safe_search_annotation:
            result = {
                "adult": safe_search_annotation.adult.name,
                "medical": safe_search_annotation.medical.name,
                "violence": safe_search_annotation.violence.name,
                "racy": safe_search_annotation.racy.name
            }
            
            # spoof/spoofed両対応
            if hasattr(safe_search_annotation, 'spoofed'):
                result["spoofed"] = safe_search_annotation.spoofed.name
            elif hasattr(safe_search_annotation, 'spoof'):
                result["spoofed"] = safe_search_annotation.spoof.name
            
            return result
        return {}
    
    def _extract_colors(self, image_properties_annotation) -> List[Dict[str, Any]]:
        """画像の色情報を抽出"""
        colors = []
        if image_properties_annotation and image_properties_annotation.dominant_colors and image_properties_annotation.dominant_colors.colors:
            for c in image_properties_annotation.dominant_colors.colors[:8]:  # 上位8色
                colors.append({
                    "rgb": {
                        "r": c.color.red, 
                        "g": c.color.green, 
                        "b": c.color.blue
                    },
                    "score": float(c.score or 0.0),
                    "pixel_fraction": float(c.pixel_fraction or 0.0)
                })
        return colors
    
    def _extract_normalized_vertices(self, bounding_poly) -> Dict[str, List[Dict[str, float]]]:
        """オブジェクト検出用の正規化頂点抽出"""
        if bounding_poly and hasattr(bounding_poly, 'normalized_vertices'):
            vertices = []
            for vertex in bounding_poly.normalized_vertices:
                vertices.append({
                    "x": vertex.x if vertex.x is not None else 0.0,
                    "y": vertex.y if vertex.y is not None else 0.0
                })
            
            return {
                "vertices": vertices,
                "coordinate_system": "normalized"
            }
        return {"vertices": [], "coordinate_system": "normalized"}
    
    def _extract_bounding_poly(self, bounding_poly, normalized: bool = True) -> Dict[str, List[Dict[str, float]]]:
        """バウンディングボックス情報を抽出（汎用）"""
        if bounding_poly:
            vertices = []
            # normalized_verticesを優先的に使用
            if hasattr(bounding_poly, 'normalized_vertices') and bounding_poly.normalized_vertices:
                for vertex in bounding_poly.normalized_vertices:
                    vertices.append({
                        "x": vertex.x if vertex.x is not None else 0.0,
                        "y": vertex.y if vertex.y is not None else 0.0
                    })
            elif hasattr(bounding_poly, 'vertices') and bounding_poly.vertices:
                for vertex in bounding_poly.vertices:
                    vertices.append({
                        "x": vertex.x if vertex.x is not None else 0.0,
                        "y": vertex.y if vertex.y is not None else 0.0
                    })
            
            return {
                "vertices": vertices,
                "coordinate_system": "normalized" if normalized else "pixel"
            }
        return {"vertices": [], "coordinate_system": "normalized" if normalized else "pixel"}
    
    def __del__(self):
        """リソースのクリーンアップ"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# シングルトンインスタンス
vision_service = VisionApiService()