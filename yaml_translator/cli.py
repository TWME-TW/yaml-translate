"""
命令行介面模塊
提供友好的命令行交互
"""

import click
import sys
import time
from pathlib import Path

from .config import Config
from .translator import YAMLTranslator


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path (default: input_translated.yaml)'
)
@click.option(
    '-l', '--language',
    type=str,
    help='Target language (e.g., zh-TW, ja, ko)'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Configuration file path (YAML format)'
)
@click.option(
    '--api-url',
    type=str,
    help='OpenAI API URL'
)
@click.option(
    '--api-key',
    type=str,
    help='OpenAI API key'
)
@click.option(
    '--model',
    type=str,
    help='Model name (e.g., gpt-4, gpt-3.5-turbo)'
)
@click.option(
    '--max-tokens',
    type=int,
    help='Maximum tokens per request'
)
@click.option(
    '--rpm-limit',
    type=int,
    help='Rate limit: requests per minute'
)
@click.option(
    '--tpm-limit',
    type=int,
    help='Rate limit: tokens per minute'
)
@click.option(
    '--test-connection',
    is_flag=True,
    help='Test API connection and exit'
)
@click.version_option(version='0.1.0', prog_name='yaml-translate')
def main(
    input_file,
    output,
    language,
    config,
    api_url,
    api_key,
    model,
    max_tokens,
    rpm_limit,
    tpm_limit,
    test_connection
):
    """
    YAML Translator - Translate YAML files using AI
    
    Example:
    
        yaml-translate input.yaml -o output.yaml -l zh-TW
    """
    try:
        # 載入配置
        cfg = Config(config_file=config)
        
        # 覆蓋命令行參數
        if api_url:
            cfg.api_url = api_url
        if api_key:
            cfg.api_key = api_key
        if model:
            cfg.model = model
        if language:
            cfg.target_language = language
        if max_tokens:
            cfg.max_tokens_per_request = max_tokens
        if rpm_limit:
            cfg.rate_limit_rpm = rpm_limit
        if tpm_limit:
            cfg.rate_limit_tpm = tpm_limit
        
        # 驗證配置
        try:
            cfg.validate()
        except ValueError as e:
            click.echo(f"❌ Configuration error: {e}", err=True)
            click.echo("\n💡 Tip: Set API_KEY in .env file or use --api-key option", err=True)
            sys.exit(1)
        
        # 創建翻譯器
        with YAMLTranslator(cfg) as translator:
            # 測試連接模式
            if test_connection:
                if translator.test_connection():
                    click.echo("✅ API connection successful!")
                    sys.exit(0)
                else:
                    click.echo("❌ API connection failed!")
                    sys.exit(1)
            
            # 確定輸出文件名
            if not output:
                input_path = Path(input_file)
                output = str(input_path.parent / f"{input_path.stem}_translated{input_path.suffix}")
            
            start_time = time.time()
            # 執行翻譯
            translator.translate_file(
                input_file=input_file,
                output_file=output,
                target_language=language
            )
            elapsed_time = time.time() - start_time
            
            click.echo(f"\n🎉 Success! Translated file saved to: {output}")
            click.echo(f"⏱️  Total time elapsed: {elapsed_time:.2f} seconds")
    
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Translation interrupted by user", err=True)
        sys.exit(130)
    
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
