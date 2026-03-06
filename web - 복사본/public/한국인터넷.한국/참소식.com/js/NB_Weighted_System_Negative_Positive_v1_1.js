// 주어진 배열들을 초기화하는 함수
function initializeArrays(count) {
    const arrays = ['BIT_START_A50', 'BIT_START_A100', 'BIT_START_B50', 'BIT_START_B100', 'BIT_START_NBA100'];
    const initializedArrays = {};
    arrays.forEach(array => {
        initializedArrays[array] = new Array(count);
    });
    return initializedArrays;
}

// N/B 값을 계산하는 함수 (음수 지원)
function calculateBit(nb, bit = 5.5, reverse = false) {
    if (nb.length < 2) {
        return bit / 100;
    }

    const BIT_NB = bit;
    const max = Math.max(...nb);
    const min = Math.min(...nb);
    const COUNT = 50;
    const CONT = 20;
    const range = max - min;
    const increment = Math.abs(range) / (COUNT * nb.length - 1); // 항상 양수로 처리
    const VIEW = BIT_NB / CONT;

    const arrays = initializeArrays(COUNT * nb.length);
    let count = 0;
    let totalSum = 0;

    for (let value of nb) {
        for (let i = 0; i < COUNT; i++) {
            const BIT_END = 1;
            const A50 = min + increment * (count + 1);
            const A100 = (count + 1) * BIT_NB / (COUNT * nb.length);
            const B50 = A50 - increment * 2;
            const B100 = A50 + increment;
            const NBA100 = A100 / (nb.length - BIT_END);

            arrays.BIT_START_A50[count] = A50;
            arrays.BIT_START_A100[count] = A100;
            arrays.BIT_START_B50[count] = B50;
            arrays.BIT_START_B100[count] = B100;
            arrays.BIT_START_NBA100[count] = NBA100;
            count++;
        }
        totalSum += value;
    }

    if (reverse) {
        arrays.BIT_START_NBA100.reverse();
    }

    let NB50 = 0;
    for (let value of nb) {
        for (let a = 0; a < arrays.BIT_START_NBA100.length; a++) {
            if (arrays.BIT_START_B50[a] <= value && arrays.BIT_START_B100[a] >= value) { // 포함 범위 조건
                NB50 += arrays.BIT_START_NBA100[Math.min(a, arrays.BIT_START_NBA100.length - 1)];
                break;
            }
        }
    }

    const BIT = Math.max((10 - nb.length) * 10, 1);
    const averageRatio = (totalSum / (nb.length * Math.abs(max))) * 100; // 절대값으로 계산
    NB50 = Math.min((NB50 / 100) * averageRatio, BIT_NB);

    
    if (nb.length === 2) {
        return bit - NB50;
    }
  
    return NB50;
}

let SUPER_BIT = 0;

// SUPER_BIT를 업데이트하는 함수
function updateSuperBit(newValue) {
    //console.log(`Updating SUPER_BIT: Previous=${SUPER_BIT}, New=${newValue}`);
    SUPER_BIT = newValue;
}

// BIT_MAX_NB 함수
function BIT_MAX_NB(nb, bit = 5.5) {
    let result = calculateBit(nb, bit, false);

    if (!isFinite(result) || isNaN(result) || result > 100 || result < -100) {
        //console.warn("Invalid BIT_MAX_NB value detected. Resetting to SUPER_BIT.");
        return SUPER_BIT;
    } else {
        updateSuperBit(result);
        return result;
    }
}

// BIT_MIN_NB 함수
function BIT_MIN_NB(nb, bit = 5.5) {
    let result = calculateBit(nb, bit, true);

    if (!isFinite(result) || isNaN(result) || result > 100 || result < -100) {
        //console.warn("Invalid BIT_MIN_NB value detected. Resetting to SUPER_BIT.");
        return SUPER_BIT;
    } else {
        updateSuperBit(result);
        return result;
    }
}

// 두 배열을 비교하여 중복 횟수와 순서를 측정하는 함수
function calculateArrayOrderAndDuplicate(nb1, nb2) {
    let orderMatch = 0;       // 순서가 일치하는 요소의 수
    let maxOrderMatch = 0;    // 가장 긴 연속된 순서 일치 요소의 수
    let duplicateMatch = 0;   // 중복값이 2번 이상인 경우에 일치하는 요소의 수
    
    const length1 = nb1.length;
    const length2 = nb2.length;

    // 중복 확인을 위한 객체 생성
    const elementCount1 = {};
    const elementCount2 = {};

    // 첫 번째 배열의 중복 횟수 계산
    nb1.forEach(value => {
        elementCount1[value] = (elementCount1[value] || 0) + 1;
    });

    // 두 번째 배열의 중복 횟수 계산
    nb2.forEach(value => {
        elementCount2[value] = (elementCount2[value] || 0) + 1;
    });

    // 중복값이 2번 이상인 경우에 일치하는지 확인
    Object.keys(elementCount1).forEach(key => {
        if (elementCount1[key] >= 1 && elementCount2[key] >= 1) {
            duplicateMatch += Math.min(elementCount1[key], elementCount2[key]);
        }
    });

    // 두 배열의 순서 및 중복 비교
    for (let i = 0; i < length1; i++) {
        for (let j = 0; j < length2; j++) {
            if (nb1[i] === nb2[j]) {
                let tempMatch = 0;
                let x = i;
                let y = j;
                
                while (x < length1 && y < length2 && nb1[x] === nb2[y]) {
                    tempMatch++;
                    x++;
                    y++;
                }

                if (tempMatch > maxOrderMatch) {
                    maxOrderMatch = tempMatch;
                }
            }
        }
    }

    orderMatch = maxOrderMatch;

    // 순서 일치 비율 계산 (백분율)
    const orderMatchRatio = (orderMatch / Math.min(length1, length2)) * 100;

    // 좌측과 우측의 중복 비율 계산
    const duplicateMatchRatioLeft = (duplicateMatch / length1) * 100;
    const duplicateMatchRatioRight = (duplicateMatch / length2) * 100;

    // 중복 일치 비율 계산 (백분율): 좌측과 우측의 중복 비율을 합산
    const duplicateMatchRatio = ( duplicateMatchRatioLeft + duplicateMatchRatioRight ) / 2;

    // 길이 비교 (두 배열의 길이 차이)
    let lengthDifference = 0;
    if(length2 < length1) {
      lengthDifference = (length2 / length1) * 100;
    } else {
      lengthDifference = (length1 / length2) * 100;
    }
  
    // 최종 결과 반환
    return {
        orderMatchRatio: orderMatchRatio,         // 순서 일치 비율
        duplicateMatchRatio: duplicateMatchRatio, // 중복 일치 비율
        duplicateMatchRatioLeft: duplicateMatchRatioLeft, // 중복 일치 비율
        duplicateMatchRatioRight: duplicateMatchRatioRight, // 중복 일치 비율
        lengthDifference: lengthDifference        // 배열 길이 차이
    };
}

// Levenshtein 거리 계산 함수
function levenshtein(a, b) {
    const matrix = [];

    // 문자열 a의 길이만큼 초기화
    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    // 문자열 b의 길이만큼 초기화
    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    // Levenshtein 거리 계산
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1, // 대체
                    Math.min(matrix[i][j - 1] + 1, // 삽입
                        matrix[i - 1][j] + 1)); // 삭제
            }
        }
    }

    return matrix[b.length][a.length];
}

// Levenshtein 기반 유사도 계산 함수
function calculateLevenshteinSimilarity(nb1, nb2) {
    let totalSimilarity = 0;

    for (let i = 0; i < nb1.length; i++) {
        let bestMatch = Infinity;

        for (let j = 0; j < nb2.length; j++) {
            const distance = levenshtein(nb1[i], nb2[j]);
            bestMatch = Math.min(bestMatch, distance);
        }

        const maxLength = Math.max(nb1[i].length, nb2[bestMatch]?.length || 1);
        const similarity = ((maxLength - bestMatch) / maxLength) * 100;
        totalSimilarity += similarity;
    }

    return totalSimilarity / nb1.length;
}


// SOUNDEX 기반 유사도 계산 함수
function calculateSoundexMatch(nb1, nb2) {
    let soundexMatch = 0;

    // 배열 요소 비교
    for (let i = 0; i < nb1.length; i++) {
        for (let j = 0; j < nb2.length; j++) {
            // SOUNDEX를 적용하여 발음 유사성 비교
            if (soundex(nb1[i]) === soundex(nb2[j])) {
                soundexMatch++;
            }
        }
    }

    // SOUNDEX 일치 비율 계산 (백분율)
    const soundexMatchRatio = (soundexMatch / Math.min(nb1.length, nb2.length)) * 100;

    return soundexMatchRatio;
}

// SOUNDEX 함수 (문자열을 발음 코드로 변환)
function soundex(s) {
    // 값이 문자열이 아닌 경우 문자열로 변환
    if (typeof s !== 'string') {
        s = String(s);
    }

    const a = s.toLowerCase().split('');
    const f = a.shift();
    const r = a
        .map(c => (/[bfpv]/.test(c) ? 1 :
                   /[cgjkqsxz]/.test(c) ? 2 :
                   /[dt]/.test(c) ? 3 :
                   /[l]/.test(c) ? 4 :
                   /[mn]/.test(c) ? 5 :
                   /[r]/.test(c) ? 6 : ''))
        .filter((v, i, arr) => i === 0 || v !== arr[i - 1])
        .join('');
    return (f + r + '000').slice(0, 4).toUpperCase();
}

function calculateBitArrayOrderAndDuplicate(nb1, nb2, bit = 5.5) {
    // 순서와 중복값, 길이 비교
    const comparisonResults = calculateArrayOrderAndDuplicate(nb1, nb2);


    // 최종 결과 반환
    return {
        orderMatchRatio: comparisonResults.orderMatchRatio,       // 순서 일치 비율
        duplicateMatchRatio: comparisonResults.duplicateMatchRatio, // 중복 일치 비율
        duplicateMatchRatioLeft: comparisonResults.duplicateMatchRatioLeft, // 좌측 중복 일치 비율
        duplicateMatchRatioRight: comparisonResults.duplicateMatchRatioRight, // 우측 중복 일치 비율
        lengthDifference: comparisonResults.lengthDifference,      // 배열 길이 차이
    };
}


function initializeArrays(length) {
  return {
    BIT_START_A50: new Array(length).fill(0),
    BIT_START_A100: new Array(length).fill(0),
    BIT_START_B50: new Array(length).fill(0),
    BIT_START_B100: new Array(length).fill(0),
    BIT_START_NBA100: new Array(length).fill(0),
  };
}

function wordSim(nbMax = 100, nbMin = 50, max = 100, min = 50) {
  let simMax = (nbMax <= max) ? (nbMax / max) * 100 : (max / nbMax) * 100;
  simMax = Math.abs(simMax) > 100 ? 100 - Math.abs(simMax) : simMax;
  if (nbMax === max) simMax = 99.99;

  let simMin = (nbMin <= min) ? (nbMin / min) * 100 : (min / nbMin) * 100;
  simMin = Math.abs(simMin) > 100 ? 100 - Math.abs(simMin) : simMin;
  if (nbMin === min) simMin = 99.99;

  let similarity = (simMax + simMin) / 2;
  return Math.abs(similarity);
}

function wordSim2(nbMax = 100, max = 100) {
  // simMax 계산
  let simMax = (nbMax <= max) ? (nbMax / max) * 100 : (max / nbMax) * 100;

  // nbMax와 max가 같으면 simMax를 99.99로 설정
  if (nbMax === max) simMax = 99.99;

  // similarity를 simMax로 설정하고 절대값 반환
  return Math.abs(simMax);
}

function calculateArraySimilarity(array1, array2) {
  // 기존 교집합/합집합 기반 유사성 계산
  let intersection = array1.filter(value => array2.includes(value));
  let union = Array.from(new Set([...array1, ...array2]));
  let jaccardSimilarity = (union.length > 0) ? (intersection.length / union.length) * 100 : 0;

  // 순서를 고려한 유사성 계산
  let orderedMatches = array1.filter((value, index) => value === array2[index]);
  let orderedSimilarity = (array1.length > 0 && array1.length === array2.length) ? (orderedMatches.length / array1.length) * 100 : 0;

  // 두 유사성을 결합하여 최종 유사성 계산
  // 여기서 50%씩 가중치를 부여하지만, 원하는 비율로 조정할 수 있음
  return (jaccardSimilarity * 0.5) + (orderedSimilarity * 0.5);
}

function areLanguagesSame(str1, str2) {
  return identifyLanguage(str1) === identifyLanguage(str2);
}

function wordNbUnicodeFormat(array) {
  if (!Array.isArray(array)) {
    array = array.split('');
  }

  const langRanges = [
    { range: [0xAC00, 0xD7AF], prefix: 1000000 }, // Korean
    { range: [0x3040, 0x309F], prefix: 2000000 }, // Japanese Hiragana
    { range: [0x30A0, 0x30FF], prefix: 3000000 }, // Japanese Katakana
    { range: [0x4E00, 0x9FFF], prefix: 4000000 }, // Chinese
    { range: [0x0410, 0x044F], prefix: 5000000 }, // Russian
    { range: [0x0041, 0x007A], prefix: 6000000 }, // English
    { range: [0x0590, 0x05FF], prefix: 7000000 }, // Hebrew
    { range: [0x00C0, 0x00FD], prefix: 8000000 }, // Vietnamese
    { range: [0x0E00, 0x0E7F], prefix: 9000000 }, // Thai
  ];

  return array.map(char => {
    const unicodeValue = char.codePointAt(0);
    const lang = langRanges.find(lang => unicodeValue >= lang.range[0] && unicodeValue <= lang.range[1]);
    const prefix = lang ? lang.prefix : 0;
    return prefix + unicodeValue;
  });
}

function calculateSimilarity(word1, word2) {
  const stageLevel = 1;

  const arrs1 = wordNbUnicodeFormat(word1);
  const nbMax = BIT_MAX_NB(arrs1);
  const nbMin = BIT_MIN_NB(arrs1);

  const arrs2 = wordNbUnicodeFormat(word2);
  const max = BIT_MAX_NB(arrs2);
  const min = BIT_MIN_NB(arrs2);

  const similarity1 = wordSim(nbMax, nbMin, max, min);
  const similarity2 = calculateArraySimilarity(arrs1, arrs2);

  if (areLanguagesSame(word1, word2)) {
    return Math.max(similarity1, similarity2) * stageLevel;
  } else {
    return Math.min(similarity1, similarity2) / stageLevel;
  }
}

function calculateSimilarity2(maxValue, minValue, firstWord, secondWord) {
  const stageLevel = 1;

  const unicodeArray1 = wordNbUnicodeFormat(firstWord);
  const unicodeArray2 = wordNbUnicodeFormat(secondWord);

  const maxBitValue = BIT_MAX_NB(unicodeArray2);
  const minBitValue = BIT_MIN_NB(unicodeArray2);

  const similarityBasedOnValues = wordSim(maxValue, minValue, maxBitValue, minBitValue);
  const similarityBasedOnArrays = calculateArraySimilarity(unicodeArray1, unicodeArray2);

  let finalSimilarity;
  if (areLanguagesSame(firstWord, secondWord)) {
    finalSimilarity = Math.max(similarityBasedOnValues, similarityBasedOnArrays) * stageLevel;
  } else {
    finalSimilarity = Math.min(similarityBasedOnValues, similarityBasedOnArrays) / stageLevel;
  }

  return {
    finalSimilarity,
    maxValue,
    minValue,
    maxBitValue,
    minBitValue
  };
}

function identifyLanguage(str) {
  const unicodeArray = str.split('');
  const languageCounts = {
    'Japanese': 0,
    'Korean': 0,
    'English': 0,
    'Russian': 0,
    'Chinese': 0,
    'Hebrew': 0,
    'Vietnamese': 0,
    'Thai': 0,
    'Portuguese': 0,
    'Others': 0,
  };

  const portugueseChars = new Set([
    0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x00CC, 0x00CD, 0x00CE,
    0x00CF, 0x00D2, 0x00D3, 0x00D4, 0x00D5, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x00DD, 0x00E0, 0x00E1, 
    0x00E2, 0x00E3, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC, 0x00ED, 0x00EE, 0x00EF, 0x00F2,
    0x00F3, 0x00F4, 0x00F5, 0x00F9, 0x00FA, 0x00FB, 0x00FC, 0x00FD, 0x0107, 0x0113, 0x012B, 0x014C,
    0x016B, 0x1ECD, 0x1ECF, 0x1ED1, 0x1ED3, 0x1ED5, 0x1ED7, 0x1ED9, 0x1EDB, 0x1EDD, 0x1EDF, 0x1EE1,
    0x1EE3, 0x1EE5, 0x1EE7, 0x1EE9, 0x1EEB, 0x1EED, 0x1EEF, 0x1EF1,
  ]);

  unicodeArray.forEach(char => {
    const unicodeValue = char.codePointAt(0);

    if (portugueseChars.has(unicodeValue)) {
      languageCounts['Portuguese']++;
      languageCounts['Portuguese'] *= 10;
    } else if (unicodeValue >= 0xAC00 && unicodeValue <= 0xD7AF) {
      languageCounts['Korean']++;
      languageCounts['Korean'] *= 100;
    } else if ((unicodeValue >= 0x3040 && unicodeValue <= 0x309F) ||
               (unicodeValue >= 0x30A0 && unicodeValue <= 0x30FF) ||
               (unicodeValue >= 0x4E00 && unicodeValue <= 0x9FFF)) {
      languageCounts['Japanese']++;
      languageCounts['Japanese'] *= 10;
    } else if (unicodeValue >= 0x4E00 && unicodeValue <= 0x9FFF) {
      languageCounts['Chinese']++;
    } else if ((unicodeValue >= 0x0041 && unicodeValue <= 0x005A) ||
               (unicodeValue >= 0x0061 && unicodeValue <= 0x007A)) {
      languageCounts['English']++;
    } else if ((unicodeValue >= 0x00C0 && unicodeValue <= 0x00FF) ||
               (unicodeValue >= 0x0102 && unicodeValue <= 0x01B0)) {
      languageCounts['Vietnamese']++;
      languageCounts['Vietnamese'] *= 10;
    } else if (unicodeValue >= 0x0410 && unicodeValue <= 0x044F) {
      languageCounts['Russian']++;
      languageCounts['Russian'] *= 10;
    } else if (unicodeValue >= 0x0590 && unicodeValue <= 0x05FF) {
      languageCounts['Hebrew']++;
      languageCounts['Hebrew'] *= 10;
    } else if (unicodeValue >= 0x0E00 && unicodeValue <= 0x0E7F) {
      languageCounts['Thai']++;
      languageCounts['Thai'] *= 10;
    } else {
      languageCounts['Others']++;
    }
  });

  const totalCharacters = Object.values(languageCounts).reduce((a, b) => a + b, 0);
  const languageRatios = {};

  for (const [key, value] of Object.entries(languageCounts)) {
    languageRatios[key] = totalCharacters > 0 ? value / totalCharacters : 0;
  }

  const sortedLanguages = Object.entries(languageRatios).sort((a, b) => b[1] - a[1]);
  const identifiedLanguage = sortedLanguages[0][0];
  const maxRatio = sortedLanguages[0][1];

  if (identifiedLanguage === 'Others' || maxRatio === 0) {
    if (sortedLanguages.length > 1) {
      const secondLanguage = sortedLanguages[1][0];
      const secondRatio = sortedLanguages[1][1];
      return secondRatio === 0 ? 'None' : secondLanguage;
    } else {
      return 'None';
    }
  }

  return identifiedLanguage;
}

function calculateSentenceBits(sentence) {
  const unicodeArray = wordNbUnicodeFormat(sentence);
  const bitMax = BIT_MAX_NB(unicodeArray);
  const bitMin = BIT_MIN_NB(unicodeArray);
  return { bitMax, bitMin };
}

function removeSpecialCharsAndSpaces(input) {
  if (input === undefined || input === null) {
    console.error('Input is undefined or null');
    return '';
  }
  
  // 연속된 공백을 하나의 공백으로 치환
  const normalizedSpaces = input.replace(/\s+/g, ' ');

  // 특수 문자 제거 ([] 제외)
  return normalizedSpaces.replace(/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ\s\[\]#]/g, '').trim();
}



function cosineSimilarity(vec1, vec2) {
  const dotProduct = (vec1, vec2) => vec1.reduce((acc, val, i) => acc + val * vec2[i], 0);
  const magnitude = vector => Math.sqrt(vector.reduce((acc, val) => acc + val * val, 0));

  const dotProd = dotProduct(vec1, vec2);
  const mag1 = magnitude(vec1);
  const mag2 = magnitude(vec2);

  return dotProd / (mag1 * mag2);
}