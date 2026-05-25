import asyncio

from app.core.config import Settings
from app.interfaces.gateways.lmstudio_gateway import LMStudioGateway


async def check_lmstudio() -> None:
    # ユーザーが指定したホスト (192.168.254.5) に向けて設定を上書き
    settings = Settings(
        llm_api_base_url="http://192.168.254.5:1234/v1",
        llm_api_key="lm-studio",
        text_model_name="local-model",  # LMStudioの場合は大抵無視されるかロード済みのものが使われます
        llm_temperature=0.0,
    )

    gateway = LMStudioGateway(settings=settings)

    test_text = """
    【転出届】
    引っ越しをする場合は、転出届を市役所市民課に提出する必要があります。
    必要な持ち物は、本人確認書類（マイナンバーカードや運転免許証）と印鑑です。
    """

    print("Sending request to LMStudio at", settings.llm_api_base_url, "...")
    try:
        result = await gateway.generate_ontology(test_text)
        print("\n=== Extraction Result ===")
        print(result.model_dump_json(indent=2))
        print("=========================")
    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(check_lmstudio())
