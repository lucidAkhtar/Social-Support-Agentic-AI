"""
OCR Configuration for M1 Hardware Optimization

This module provides optimized OCR settings for running on Apple Silicon (M1)
with limited RAM (8GB). Configurations balance accuracy with performance.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRConfig:
    """Configuration for optimized OCR on M1 hardware."""
    
    # Image preprocessing
    max_image_width: int = 2000
    max_image_height: int = 2000
    auto_contrast: bool = True
    convert_to_grayscale: bool = True
    denoise: bool = False  # Can be slow on M1
    
    # Tesseract configuration
    lang: str = "eng"  # Language configuration
    config_string: str = "--psm 3 --oem 3"  # PSM 3 = auto page segmentation, OEM 3 = legacy+LSTM
    
    # Performance tuning
    timeout_seconds: int = 30  # Maximum time per image
    batch_size: int = 5  # Process N images before clearing cache
    
    # Quality thresholds
    min_confidence: float = 0.5  # Minimum acceptable OCR confidence
    min_text_length: int = 10  # Minimum characters to consider valid extraction
    
    # M1-specific optimizations
    use_metal: bool = True  # Use Metal for GPU acceleration (if available)
    memory_efficient: bool = True  # Enable memory-efficient processing
    cache_size_mb: int = 256  # Cache size in MB (limited on 8GB system)
    
    def get_tesseract_config(self) -> str:
        """Get complete Tesseract configuration string."""
        return f"{self.config_string}"
    
    def should_process_image(self, file_size_mb: float) -> bool:
        """Check if image should be processed based on size constraints."""
        # Skip images larger than 50MB (unusual for ID documents)
        return file_size_mb < 50


# Default M1 configuration
M1_OPTIMIZED = OCRConfig(
    max_image_width=1800,  # Slightly reduced to save memory
    max_image_height=1800,
    auto_contrast=True,
    convert_to_grayscale=True,
    lang="eng",
    config_string="--psm 3 --oem 3",
    timeout_seconds=30,
    batch_size=5,
    min_confidence=0.5,
    min_text_length=10
)

# High accuracy configuration (slower, more resource intensive)
HIGH_ACCURACY = OCRConfig(
    max_image_width=2400,
    max_image_height=2400,
    auto_contrast=True,
    convert_to_grayscale=False,
    denoise=True,
    lang="eng",
    config_string="--psm 1 --oem 3",  # PSM 1 = orientation detection
    timeout_seconds=60,
    batch_size=2,
    min_confidence=0.7,
    min_text_length=15
)

# Fast configuration (speed over accuracy)
FAST = OCRConfig(
    max_image_width=1200,
    max_image_height=1200,
    auto_contrast=False,
    convert_to_grayscale=True,
    lang="eng",
    config_string="--psm 3 --oem 1",  # OEM 1 = legacy only
    timeout_seconds=10,
    batch_size=10,
    min_confidence=0.4,
    min_text_length=5
)


class OCROptimizer:
    """Utility class for OCR optimization on M1 hardware."""
    
    @staticmethod
    def select_config(
        mode: str = "balanced",
        available_ram_gb: float = 8.0,
        target_speed_ms: Optional[int] = None
    ) -> OCRConfig:
        """
        Select optimal OCR configuration based on available resources.
        
        Args:
            mode: "fast", "balanced", "accurate"
            available_ram_gb: Available RAM in GB (for optimization)
            target_speed_ms: Target processing time per image in milliseconds
        
        Returns:
            Optimized OCRConfig
        """
        if mode == "fast":
            return FAST
        elif mode == "accurate":
            return HIGH_ACCURACY
        else:  # balanced
            config = M1_OPTIMIZED.copy() if hasattr(M1_OPTIMIZED, 'copy') else OCRConfig(**vars(M1_OPTIMIZED))
            
            # Adjust batch size based on RAM
            if available_ram_gb < 6:
                config.batch_size = 2
                config.max_image_width = 1400
                config.max_image_height = 1400
            elif available_ram_gb > 12:
                config.batch_size = 10
            
            return config
    
    @staticmethod
    def estimate_processing_time(
        image_count: int,
        config: OCRConfig,
        avg_image_size_mb: float = 2.0
    ) -> dict:
        """
        Estimate total processing time for a batch of images.
        
        Args:
            image_count: Number of images to process
            config: OCR configuration
            avg_image_size_mb: Average image file size
        
        Returns:
            Dictionary with timing estimates
        """
        # Estimate ~100-500ms per image depending on config
        if config == FAST:
            per_image_ms = 150
        elif config == HIGH_ACCURACY:
            per_image_ms = 400
        else:
            per_image_ms = 250
        
        total_ms = image_count * per_image_ms
        
        return {
            "per_image_ms": per_image_ms,
            "total_ms": total_ms,
            "total_seconds": total_ms / 1000,
            "batches": (image_count + config.batch_size - 1) // config.batch_size,
            "bytes_per_image": int(avg_image_size_mb * 1024 * 1024)
        }
