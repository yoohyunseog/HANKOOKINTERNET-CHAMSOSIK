

// 장르 코드와 이름을 매핑하는 객체
const genreMap = {
    "CosmeticBrandsInfo": "선물 추천을 위한 화장품 브랜드 정보를 알려주세요",
    "DongmyoFashionHub": "인테리어 아이디어와 최신 트렌드를 알려주세요. 준비 비용과 예상 기간도 함께 알려주세요.",
    "TourSpots": "가볼 만한 여행지나 이벤트가 있나요? 행사명, 기간, 위치를 알려주세요.",
    "Organizers": "공연이나 콘서트의 장소 및 티켓 예매 정보가 있나요?",
    "PsychologyResources": "마음을 다스릴 수 있는 심리학 자료가 있나요? 운세도 알려주세요.",
    "Semiraepaong": "준비에 도움되는 인플루언서의 인스타그램 스토리를 알려주세요. 인스타그램 주소도 공유해 주세요.",
    "stock": "연말 주식 시장과 코스피 동향은 어떤가요? 추천하는 코스피 종목이 있나요?",
    "CommGuide": "모임을 위한 효과적인 대화법이나 커뮤니케이션 가이드라인을 알려주세요.",
    "car": "선물로 적합한 중고차와 신차의 가격을 비교해 주세요.",
    "PokemonBread": "특별 할인 상품과 회원권 정보가 있나요? 케이크 레시피가 있다면 재료 가격과 저렴한 할인마트 정보를 알려주세요.",
    "GameNews": "기념한 게임 업데이트와 관련 소식을 알려주세요. 이벤트 공략이나 팁도 있으면 좋겠습니다.",
    "FashionMakersList": "선물로 추천하는 제품의 이름과 가격은 어떻게 되나요?",
    "entertainment": "특집 영상 콘텐츠를 시청할 수 있는 OTT 플랫폼이나 방송 채널을 알려주세요.",
    "RecommendedVideo": "관련된 최신 소식과 기사를 알려주세요.",
    "anime": "테마의 애니메이션이나 웹툰을 시청할 수 있는 OTT 플랫폼이나 방송 채널을 알려주세요. 관련 피규어 제품명과 가격도 부탁드립니다.",
    "DramaDetails": "볼 만한 드라마를 시청할 수 있는 OTT 플랫폼 또는 방송 채널을 알려주세요.",
    "movie": "영화 콘텐츠를 시청할 수 있는 OTT 플랫폼 또는 방송 채널을 알려주세요."
};
   
function getGenreName(Get_genre, genreCode, getStr) {
    // getStr 문장 끝에 ? 가 있으면 빈 문자열 반환
    if (getStr && getStr.trim().endsWith('?')) {
        return '';
    }
    
    if (Get_genre === 'RecommendedVideo') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'car') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'anime') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'CommGuide') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'stock') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'Semiraepaong') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'PsychologyResources') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'FashionMakersList') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'movie') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'DramaDetails') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'anime') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'PokemonBread') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'Organizers') {
        genreCode = Get_genre;
    }

    if (Get_genre === 'TourSpots') {
        genreCode = Get_genre;
    }
    
    if (Get_genre === 'DongmyoFashionHub') {
        genreCode = Get_genre;
    }
    
    if (!genreMap[genreCode]) {
        genreCode = Get_genre;
    }

    console.log('맵 출력', genreMap);
    console.log('현재 장르 출력', Get_genre);
    console.log('해당 장르의 맵 출력', genreMap[genreCode]);
    console.log('해당 장르 출력', genreCode);

    // 장르 코드에 해당하는 이름 반환
    return genreMap[genreCode] || " 이 컨텐츠를 시청할 수 있는 OTT 플랫폼이나 방송 채널의 링크를 모두 제공해 주세요. 블로그나 기사는 제외해주세요."; // 매핑되지 않은 경우 기본값 반환
}
