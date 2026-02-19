const { Engine, World, Bodies, Body } = Matter;

// Matter.js 물리 엔진 및 월드
let engine; // Matter.js 엔진 객체
let world; // Matter.js 월드 객체

// 차량 데이터 관리
let primaryCarData = []; // 단일 차량의 학습 데이터를 저장하는 배열 (숫자만 저장, 최대 15개)
let primaryCar; // 현재 차량 객체 (자동 주행 학습 및 시뮬레이션용)
let maxPrimaryCar = 18; // primaryCarData 배열의 최대 크기
let saveCooldown = 0; // 저장 대기 시간을 관리하는 변수

// 모델 및 학습 데이터 관리
let model; // 머신러닝 모델 객체 (속도 및 방향 예측)
let steeringSpeed = []; // 차량 조향 속도 데이터를 저장하는 배열

// 기타 시뮬레이션 요소
let treasureHandler; // 보물 상자 관련 이벤트를 처리하는 핸들러 변수
let contRoler = true; // 사용자 제어 여부를 나타내는 플래그 (true: 활성화)

// 학습 상태 관리
let isTraining = false; // 학습 상태를 나타내는 플래그 (기본값: 비활성화)

// 차량 상태 관리
let isCarOut = true; // 차량이 경계선 false true

// 초기 학습 상태를 저장하는 변수 (기본값: false)
let trainingMode = false;

let segmentLengths = []; // 각 점선 구간의 길이를 저장
let segmentAngles = [];  // 각 점선 구간의 각도를 저장

let segmentLengthsBitMax = 0; // segmentLengths의 최대값 저장
let segmentLengthsBitMin = 0; // segmentLengths의 최소값 저장

let segmentAnglesBitMax = 0; // segmentAngles의 최대값 저장
let segmentAnglesBitMin = 0; // segmentAngles의 최소값 저장

//const indexDBName = 'CarSimulationDB';
//const indexDBModel = 'speed-direction-model';

const indexDBVersion = 'Version 0.5';
const indexDBName = 'VehicleDynamicsDB'+indexDBVersion;
const indexDBModel = 'velocity-orientation-model '+indexDBVersion;

let indexLine = 0;

let indexConsole = "";
let indexState = true;

let indexangleDifference = 0;

window.onload = async function() {
  console.log("페이지가 로드되었습니다. 모델을 불러옵니다...");
  model = await loadModelFromIndexedDB();
  if (!model) {
    console.warn("IndexedDB에 저장된 모델이 없습니다. 기본 모델을 생성합니다...");
    model = createDefaultModel();
    await saveModelToIndexedDB(model);
  }
};

// =====================================
// 1. 초기 설정 및 초기화 관련
// =====================================

/**
 * URL의 파라미터를 읽어 자율주행 모드 여부를 반환
 * @returns {boolean} autoDrive 상태
 */
function getAllURLParameters() {
  const urlParams = new URLSearchParams(window.location.search);
  const params = {};
  for (const [key, value] of urlParams.entries()) {
    params[key] = value; // 키-값 쌍으로 객체에 저장
  }
  if(params['autoDrive'] === 'true') {
    isTraining = true;
  }
  return params['autoDrive'] === 'true';
}

/**
 * 초기 설정 및 엔진, 월드 생성
 */
let consoleDiv; // 콘솔창을 나타낼 변수
function setup() {
  const padding = 25; // 패딩 값
  createCanvas(windowWidth - padding * 2, windowHeight - padding * 2);
  const canvas = document.querySelector("canvas");
  canvas.style.position = "absolute";
  canvas.style.left = `${padding}px`;
  canvas.style.top = `${padding}px`;
  
  engine = Engine.create();
  world = engine.world;
  engine.world.gravity.y = 0;

  primaryCar = {
    position: { x: width / 2, y: height }, // 현재 위치
    speed: 0, // 속도
    direction: -PI / 2, // 방향
    sensor: {
      previousPosition: { x: width / 2, y: height / 2 }, // 이전 위치
      totalDistance: 0, // 총 이동 거리
    },
    initialPosition: { x: width / 2, y: height / 2 }, // 초기 위치 저장
    bit_max_nb: 0, 
    bit_max_nb: 0, 
  };
  
  primaryCar.penaltyPoints = 0;
  
  newCar = {
    position: { x: width / 2, y: height / 2 }, // 현재 위치
    speed: 0, // 속도
    direction: -Math.PI / 2, // 방향
    sensor: {
      previousPosition: { x: width / 2, y: height / 2 }, // 이전 위치
      totalDistance: 0, // 총 이동 거리
    },
    initialPosition: { x: width / 2, y: height / 2 }, // 초기 위치 저장
    bit_max_nb: 0,
    bit_min_nb: 0, // 이 부분에서 key 이름이 중복되었으므로 수정
  };
  
  newCar.penaltyPoints = 0;
  
  Engine.run(engine);
}

// 콘솔창에 메시지를 출력하는 함수
function logToConsole(message) {
  if (consoleDiv) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0]; // 현재 시간 (hh:mm:ss)
    const newLog = document.createElement('div');
    newLog.textContent = `${timestamp} - ${message}`;
    consoleDiv.appendChild(newLog);

    // 스크롤을 항상 가장 아래로 이동
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
  }
}

/**
 * 페이지 새로고침 함수
 * @param {boolean} isTrue - true이면 페이지를 새로고침
 */
function refreshPage(isTrue) {
  if(isTrue === true) {
      console.log("3초 후에 페이지가 새로고침됩니다...");
      let countdown = 3;
      const interval = setInterval(() => {
        console.log(`새로고침까지 ${countdown}초 남았습니다.`);
        countdown--;

        if (countdown <= 0) {
          clearInterval(interval);
          location.reload(); // 페이지 새로고침
        }
      }, 1000);
    }
}

// =====================================
// 2. 모델 생성 및 관리
// =====================================

/**
 * 기본 TensorFlow 모델 생성 함수 (에러 발생 시 사용)
 * @returns {tf.Sequential} 기본 모델
 */
function createDefaultModel() {
  const model = tf.sequential();

  // 입력층 + 첫 번째 은닉층
  model.add(tf.layers.dense({
    inputShape: [6], // 입력 특징의 수를 6으로 변경
    units: 32, // 은닉층 유닛 수 증가
    activation: "relu",
    kernelRegularizer: tf.regularizers.l2({ l2: 0.01 }), // L2 규제화 추가
  }));

  // 두 번째 은닉층
  model.add(tf.layers.dense({
    units: 16,
    activation: "relu",
    kernelRegularizer: tf.regularizers.l2({ l2: 0.01 }), // L2 규제화 추가
  }));

  // 드롭아웃: 과적합 방지
  model.add(tf.layers.dropout({ rate: 0.3 })); // 30% 드롭아웃

  // 세 번째 은닉층
  model.add(tf.layers.dense({
    units: 8,
    activation: "relu",
  }));

  // 출력층
  model.add(tf.layers.dense({
    units: 3, // 예측할 값의 개수 (penaltyPoints, predictedSpeed, predictedDirection)
    activation: "linear", // 출력층은 선형 활성화 함수 사용
  }));

  // 모델 컴파일
  model.compile({
    optimizer: tf.train.adam(0.001), // 학습률 조정
    loss: (predicted, actual) => {
      const penaltyLoss = tf.losses.meanSquaredError(predicted.slice([0], [1]), actual.slice([0], [1]));
      const speedLoss = tf.losses.meanSquaredError(predicted.slice([1], [1]), actual.slice([1], [1]));
      const directionLoss = tf.losses.meanSquaredError(predicted.slice([2], [1]), actual.slice([2], [1]));
      return penaltyLoss * 5 + speedLoss + directionLoss;
    },
    metrics: ["mse"], // 평균 제곱 오차를 지표로 사용
  });

  console.log("입력 특징 수 6에 맞는 모델이 생성되었습니다.");
  return model;
}



/**
 * TensorFlow 모델을 IndexedDB에 저장
 * @param {tf.Sequential} model - 저장할 모델
 */
async function saveModelToIndexedDB(model) {
  try {
    await model.save('indexeddb://'+indexDBModel);
    console.log('모델이 IndexedDB에 성공적으로 저장되었습니다.');
  } catch (error) {
    console.error('IndexedDB에 모델 저장 중 오류 발생:', error);
  }
}

/**
 * IndexedDB에서 TensorFlow 모델을 로드
 * @returns {Promise<tf.Sequential>} 로드된 모델
 */
async function loadModelFromIndexedDB() {
  try {
    const model = await tf.loadLayersModel("indexeddb://"+indexDBModel);
    console.log("IndexedDB에서 모델을 불러왔습니다.");
    model.compile({ 
      optimizer: tf.train.adam(0.001), 
      loss: "meanSquaredError", 
      metrics: ["mse"] 
    });
    return model;
  } catch (error) {
    console.warn("IndexedDB에서 모델을 찾을 수 없습니다. 새 모델을 생성합니다...");
    const newModel = createDefaultModel();
    await saveModelToIndexedDB(newModel);
    return newModel;
  }
}


/**
 * 차량 데이터를 사용해 모델을 학습
 * @param {Array} primaryCarData - 학습 데이터
 * @param {Object} primaryCar - 차량 데이터
 */
let modelIsTraining = false;

async function trainModelWithSpeed(primaryCarData, primaryCar) {
    if (modelIsTraining) {
        console.log("현재 모델이 학습 중입니다. 학습이 끝날 때까지 기다리세요.");
        return;
    }

    modelIsTraining = true; // 학습 시작
    const { features, labels } = prepareDataForSpeedLearning(primaryCarData, primaryCar);

    const featureTensor = tf.tensor2d(features);
    const labelTensor = tf.tensor2d(labels);

    console.log("모델 학습 시작...");

    // 사용자 정의 콜백 작성
    const customCallback = {
        onEpochEnd: async (epoch, logs) => {
            //console.log(`Epoch ${epoch + 1} 종료 - loss: ${logs.loss}, val_loss: ${logs.val_loss}`);
        },
        onTrainEnd: async () => {
            console.log("모델 학습 완료!");
        }
    };

    try {
        // 가중치를 데이터에 직접 반영
        const adjustedFeatures = features.map((feature, index) => {
            const bitMaxWeight = feature[0] || 0; // bit_max_nb 값
            const bitMinWeight = 1 / Math.abs(feature[1] + 1) || 0; // bit_min_nb 값 (작을수록 큰 값)
            const weight = bitMaxWeight + bitMinWeight; // 가중치 계산

            return feature.map(value => value * weight); // 각 feature 값을 가중치로 조정
        });

        const adjustedLabels = labels.map((label, index) => {
            const bitMaxWeight = features[index][0] || 0; // bit_max_nb 값
            const bitMinWeight = 1 / Math.abs(features[index][1] + 1) || 0; // bit_min_nb 값 (작을수록 큰 값)
            const weight = bitMaxWeight + bitMinWeight; // 가중치 계산

            return label.map(value => value * weight); // 각 label 값을 가중치로 조정
        });

        // 텐서 변환
        const adjustedFeatureTensor = tf.tensor2d(adjustedFeatures);
        const adjustedLabelTensor = tf.tensor2d(adjustedLabels);

        console.log("가중치를 반영한 데이터 생성 완료");

        // 모델 학습
        await model.fit(adjustedFeatureTensor, adjustedLabelTensor, {
            epochs: 50,
            batchSize: 128,
            validationSplit: 0.2,
            callbacks: customCallback
        });

        console.log("학습 완료");
    } catch (error) {
        console.error("학습 중 오류 발생:", error);
    } finally {
        modelIsTraining = false; // 학습 종료

        // 자원 정리
        featureTensor.dispose();
        labelTensor.dispose();
        console.log("Tensor 리소스 해제 완료");
    }
}

/**
 * 주행 데이터를 학습을 위한 형식으로 변환
 * @param {Array} primaryCarData - 차량 데이터
 * @param {Object} primaryCar - 차량 정보
 * @returns {Object} { features, labels }
 */
function normalizeValue(value, min, max) {
  if (value === undefined || value === null) return 0; // 결측값 처리
  return (value - min) / (max - min);
}

function normalizeValue(value, min, max) {
  if (value === undefined || value === null) return 0; // 결측값 처리
  return (value - min) / (max - min); // 정규화
}

function prepareDataForSpeedLearning(primaryCarData, primaryCar) {
  const features = [];
  const labels = [];

  const addData = (car) => {
    if (!car || typeof car !== "object") {
      console.warn("Invalid car data:", car);
      return;
    }

    // 비트 값은 정규화하지 않음
    const bitMaxNb = car.bit_max_nb || 0;
    const bitMinNb = car.bit_min_nb || 0;

    // 속도는 -5 ~ 5 범위로 정규화
    const normalizedSpeed = normalizeValue(car.speed, -5, 5);

    // 방향은 -π ~ π 범위로 정규화
    const normalizedDirection = normalizeValue(car.direction, -3.14, 3.14);
    
    // 패널티 포인트는 0 ~ 100 범위로 정규화
    const normalizedPenaltyPoints = normalizeValue(car.penaltyPoints, 0, 100);
    
    // 패널티 증가 확률 (기본값 설정)
    const penaltyIncreaseProbability = normalizeValue(car.penaltyIncreaseProbability || 0, 0, 100);

    // nb_bit 증가 확률 (기본값 설정)
    const nbBitIncreaseProbability = normalizeValue(car.bitIncreaseProbability || 0, 0, 100);

    // Feature 추가 예측할 때 필요한 입력 데이터
    features.push([
        bitMaxNb, // 비트 최대값
        bitMinNb, // 비트 최소값
        normalizedSpeed, // 정규화된 속도
        normalizedDirection, // 정규화된 방향
        penaltyIncreaseProbability, // 패널티 증가 확률
        nbBitIncreaseProbability, // nb_bit 증가 확률
    ]);

    // Label 추가
    labels.push([
        car.penaltyPoints || 0, // 패널티 포인트
        normalizedSpeed, // 정규화된 속도
        normalizedDirection, // 정규화된 방향
    ]);
  };

  // primaryCarData 배열 처리
  const primaryCarDataArray = Array.isArray(primaryCarData) ? primaryCarData : [];
  primaryCarDataArray.forEach(addData);

  // primaryCar 추가
  if (primaryCar) addData(primaryCar);

  return { features, labels };
}


/**
 * 차량의 Penalty, Speed, Direction 예측
 * @param {Object} primaryCar - 차량 정보
 * @returns {Promise<Object>} 예측 결과
 */
async function predictPenaltyPoints(primaryCar) {
  if (!model) {
    console.error('모델이 로드되지 않았습니다.');
    return;
  }

  const inputFeatures = tf.tensor2d([[ 
    primaryCar.bit_max_nb,
    primaryCar.bit_min_nb,
    primaryCar.speed,
    primaryCar.direction,
  ]]);

  const predictions = model.predict(inputFeatures);
  const values = await predictions.data();

  inputFeatures.dispose();

  return {
    penaltyPoints: values[0],
    predictedSpeed: values[1],
    predictedDirection: values[2],
  };
}

async function predictLowestPenaltyBasedOnBits(cars) {
  if (!model) {
    console.error('모델이 로드되지 않았습니다.');
    return;
  }

  // cars가 배열이 아닌 경우 배열로 변환
  if (!Array.isArray(cars)) {
    console.warn('cars가 배열이 아니어서 배열로 변환합니다.');
    cars = [cars];
  }

  // `bit_max_nb`, `bit_min_nb`, `speed`, `direction` 값으로 입력 데이터 생성
  const inputs = cars.map(car => [
    car.bit_max_nb || 0, // bit_max_nb 값
    car.bit_min_nb || 0, // bit_min_nb 값
    car.speed || 0,      // speed 기본값
    car.direction || 0,  // direction 기본값
    car.penaltyIncreaseProbability || 0, // 패널티 증가 확률
    car.nbBitIncreaseProbability || 0,  // nb_bit 증가 확률
  ]);

  // 입력 데이터를 Tensor로 변환
  const inputTensor = tf.tensor2d(inputs);

  try {
    // 모델 예측
    const predictions = model.predict(inputTensor);
    const values = await predictions.array(); // 예측 결과 배열로 변환

    // Tensor 메모리 해제
    inputTensor.dispose();

    // 패널티 점수 계산 (첫 번째 출력 값 사용)
    const penaltyPoints = values.map(v => v[0]);

    // 가장 낮은 패널티 점수의 인덱스 찾기
    const minPenaltyIndex = penaltyPoints.indexOf(Math.min(...penaltyPoints));

    // 패널티가 가장 낮은 차량 정보 반환
    const lowestPenaltyCar = {
      car: cars[minPenaltyIndex], // 차량 데이터
      penaltyPoints: penaltyPoints[minPenaltyIndex], // 최소 패널티 점수
    };

    console.log('패널티가 가장 낮은 차량:', lowestPenaltyCar);
    return lowestPenaltyCar;

  } catch (error) {
    console.error("예측 중 오류 발생:", error);
    inputTensor.dispose(); // Tensor 메모리 해제
  }
}

// =====================================
// 3. 차량 상태 업데이트 및 주행 로직
// =====================================

// 차량 상태 업데이트 관련

/**
 * 차량 경로와 상태를 업데이트
 * @param {Object} car - 차량 데이터
 * @param {Array} laneBoundsX - 차선 경계
 * @param {number} goalY - 목표 Y 좌표
 */
function updateCarPath(car, laneBoundsX, goalY) {
  const isOutOfLane = isCarOutOfLane(car); // 차선 이탈 상태 확인

  // 차량의 위치 업데이트
  car.position.x += Math.cos(car.direction) * car.speed;
  car.position.y += Math.sin(car.direction) * car.speed;

  // 패널티 및 보상 처리
  if (isOutOfLane) {
    //car.penaltyPoints -= 0.01; // 차선 이탈 패널티
  }

  // 속도 제한 패널티
  if (car.speed > 5) {
    //car.penaltyPoints -= Math.min((car.speed - 5) * 0.02, 0.1);
  }

  // 충돌 위험 패널티
  const frontDistance = calculateSensorDistances(car).front;
  if (frontDistance < 50) {
    //car.penaltyPoints -= Math.min((50 - frontDistance) / 1000, 0.01);
  }
}

/**
 * 차량 상태를 업데이트하고 패널티 처리
 * @param {Object} distances - 센서 거리 데이터
 * @param {number} penaltyAdjustmentFactor - 패널티 조정 값
 * @returns {boolean} 차선 이탈 여부
 */
function updateCarState(distances, penaltyAdjustmentFactor = 1) {
  const now = millis(); // 현재 시간(ms 단위)
  
  // 차량이 차선을 벗어났는지 확인
  const isOutOfLane = isCarOutOfLane(primaryCar);

  if (isOutOfLane) {
    //console.log("차량이 차선을 벗어났습니다!");

    // 차선을 벗어난 시간이 패널티 -10 이하인지 확인
    if (primaryCar.penaltyPoints < -10) { 
      console.log("차량이 패널티 차선을 벗어나 초기화가 진행됩니다.");
      checkAndResetCarPosition(primaryCar); // 차량 위치 초기화
    }

    return false; // 차선을 벗어남
  } else {
   //console.log("차량이 차선 안에 있습니다.");
    
     checkAndResetCarPosition(primaryCar); // 차량 위치 초기화

    return true; // 차선을 벗어나지 않음
  }
}

/**
 * 차량이 경계선을 벗어났는지 확인 후 위치 초기화
 * @param {Object} car - 차량 데이터
 * @param {number} point - 초기화 기준 점수
 */
function checkAndResetCarPosition(car) {
  const boundaryPadding = 25; // 경계선 근처에서 초기화하는 패딩 값
  const leftBoundary = boundaryPadding;
  const rightBoundary = width - boundaryPadding;
  const topBoundary = boundaryPadding + 55;
  const bottomBoundary = height - boundaryPadding;

  // 경계선 근처에 있는지 체크
  const isNearBoundary = 
    car.position.x <= leftBoundary || 
    car.position.x >= rightBoundary || 
    car.position.y <= topBoundary || 
    car.position.y >= bottomBoundary;

  // 경계선 방향별 체크
  const isAboveTopBoundary = car.position.y <= topBoundary; // 윗쪽 경계선
  const isBelowBottomBoundary = car.position.y >= bottomBoundary; // 아래쪽 경계선
  const isLeftBoundary = car.position.x <= leftBoundary; // 왼쪽 경계선
  const isRightBoundary = car.position.x >= rightBoundary; // 오른쪽 경계선

  if (isNearBoundary && car.penaltyPoints < 0.00005) {

    // 속도 및 방향 초기화
    //car.speed = 0;
    //car.direction = -PI / 2;

    // 윗쪽 경계선: 보상 trainingMode === true
    if (isAboveTopBoundary) {
      car.penaltyPoints += point;
      console.log("자동차가 윗쪽 경계선에 도달했습니다. 보상 점수를 추가합니다.");
        //car.position.x = Math.random() * width
        //car.position.y = Math.random() * height
      /*
      if(trainingMode === true || getAllURLParameters()) {
        car.position.x = Math.random() * width
        car.position.y = Math.random() * height
      } else {
        // 자동차 위치를 화면 중앙으로 초기화
        car.position.x = width / 2
        car.position.y = height - 30;
      }
      */
    } 
    // 아래쪽, 왼쪽, 오른쪽 경계선: 감점
    else if (isBelowBottomBoundary && car.penaltyPoints < -10) {
      console.log("자동차가 아래쪽 경계선에 도달했습니다. 감점 점수를 적용합니다.");
        car.speed = 5;
    } else if (isLeftBoundary) {
      car.penaltyPoints -= point;
      console.log("자동차가 왼쪽 경계선에 도달했습니다. 감점 점수를 적용합니다.");
        car.speed = 5;
    } else if (isRightBoundary) {
      car.penaltyPoints -= point;
      console.log("자동차가 오른쪽 경계선에 도달했습니다. 감점 점수를 적용합니다.");
        car.speed = 5;
    } else {
      console.log("자동차가 경계선에 도달했습니다. 위치를 초기화합니다.");
        car.speed = 5;
    }
  }
}

/**
 * 차량이 경계선을 벗어나지 않도록 제한
 * @param {Object} car - 차량 데이터
 */
function constrainCarToBounds(car) {
  car.position.x = Math.max(0, Math.min(car.position.x, width));
  car.position.y = Math.max(0, Math.min(car.position.y, height));
}

/**
 * 차량 센서 데이터를 업데이트
 * @param {Object} car - 차량 데이터
 */
function updateSensorData(car) {
  const dx = car.position.x - car.sensor.previousPosition.x;
  const dy = car.position.y - car.sensor.previousPosition.y;
  const distance = Math.sqrt(dx * dx + dy * dy); // 피타고라스 정리로 거리 계산

  // 총 이동 거리 업데이트
  car.sensor.totalDistance += distance;

  // 이전 위치 갱신
  car.sensor.previousPosition = { ...car.position };
}

/**
 * 차량 데이터를 업데이트하고 배열에 저장
 */
function updatePrimaryCarData() {
  // 숫자 데이터를 추출
  const carDataAsNumbers = [
    primaryCar.position.x,
    primaryCar.position.y,
    primaryCar.speed,
    primaryCar.direction,
  ];

  // 센서로 경계선과의 거리 계산
  const sensorDistances = calculateSensorDistances(primaryCar);
  
    // primaryCarData 업데이트
    primaryCarData.vehicleStatus = {
      directionClockNumber: radiansToClockNumber(primaryCar.direction),
      speed: primaryCar.speed, // 현재 차량의 속도 (Speed)
      direction: primaryCar.direction, // 현재 차량의 핸들링 (Handling)
      brakeStatus: 0, // 현재 차량의 브레이크 상태 (Brake Status) - 0: 비활성, 1: 활성
      BrakePressure: 0, // 브레이크 압력 (Brake Pressure) - 기본값 0
      EnginePower: 0, // 엔진 출력 (Engine Power) - 초기값 0
      TireCondition: 100, // 타이어 상태 (Tire Condition) - 100: 새 타이어, 낮을수록 마모
      StabilityControlStatus: 1, // 차량 안정성 제어 상태 (Stability Control Status) - 1: 활성, 0: 비활성
      TractionControlStatus: 1, // 트랙션 제어 상태 (Traction Control Status) - 1: 활성, 0: 비활성
      FuelLevel: 100, // 차량의 연료 상태 (Fuel Level) - 100: 만땅, 0: 비어 있음
      AccelerationX: primaryCar.speed * Math.cos(primaryCar.direction), // 현재 가속도 X (Acceleration X)
      AccelerationY: primaryCar.speed * Math.sin(primaryCar.direction), // 현재 가속도 Y (Acceleration Y)
      distanceFromInitial: primaryCar.distanceFromInitial, // 예비 데이터 1: 센서를 통한 이동 거리
      front: sensorDistances.front, // 예비 데이터 2: 정면 거리
      back: sensorDistances.back, // 예비 데이터 3: 후면 거리
      left: sensorDistances.left, // 예비 데이터 4: 좌측 거리
      right: sensorDistances.right, // 예비 데이터 5: 우측 거리
    };
 
    primaryCarData['bit_max_nb'] = primaryCar.bit_max_nb;
    primaryCarData['bit_min_nb'] = primaryCar.bit_min_nb;
    primaryCarData.penaltyPoints =   primaryCar.penaltyPoints;
  
  // 최신 maxPrimaryCar 개의 데이터만 유지
  while (primaryCarData.length > maxPrimaryCar) {
    primaryCarData.shift();
  }
}

// 차량 주행 관련 로직


/**
 * 직선 점선 경로를 그리는 함수
 * @param {number} x1 - 시작 점 X 좌표
 * @param {number} y1 - 시작 점 Y 좌표
 * @param {number} x2 - 끝 점 X 좌표
 * @param {number} y2 - 끝 점 Y 좌표
 */
function drawStraightDashedLine(x1, y1, x2, y2) {
  const dashLength = 15; // 점선 길이
  const gapLength = 10; // 점선 간 간격
  const lineLength = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
  const numDashes = Math.floor(lineLength / (dashLength + gapLength));
  const dashedPoints = []; // 점선 세그먼트 좌표 저장 배열

  for (let i = 0; i < numDashes; i++) {
    const tStart = i / numDashes;
    const tEnd = (i + 0.5) / numDashes;

    // 점선 세그먼트 시작점과 끝점 계산
    const startX = x1 + (x2 - x1) * tStart;
    const startY = y1 + (y2 - y1) * tStart;
    const endX = x1 + (x2 - x1) * tEnd;
    const endY = y1 + (y2 - y1) * tEnd;

    // 세그먼트의 시작점과 끝점 저장
    dashedPoints.push({ startX, startY, endX, endY });
  }
  
  return dashedPoints;
}


/**
 * 목표 지점으로 차량을 이동
 * @param {Object} car - 차량 데이터
 * @param {Array} laneBoundsX - 차선 경계
 * @param {number} goalY - 목표 Y 좌표
 */
function navigateToSingleGoal(car, laneBoundsX, goalY, speedIncrement, boundx = 2) {
  // 차량의 초기 목표 지점 계산
  const useRecovery = false; // 리커버리 사용 여부를 설정 (true: 활성화, false: 비활성화)

  let recoveryPoint;
  let totalDashedLength;
  
  if (useRecovery) {
    recoveryPoint = findClosestLanePoint(car, laneBoundsX, car.position.y, 1.9);
  }
  const goalPoint = { x: laneBoundsX, y: goalY };

  car.initialGoalX = car.initialGoalX || goalPoint.x;

  // 경로 시각화
  if (useRecovery && recoveryPoint && dashedSegments.length < 10) {
    // 복구 지점과 목표 지점 모두 사용
    drawBezierPathWithColorChange(car, recoveryPoint, goalPoint);
    totalDashedLength = drawDashedBezierPathWithOffset(car, recoveryPoint, goalPoint, 15, 10, 5, 2);
  } else {
    // 복구 지점 없이 목표 지점으로 바로 이동
    drawBezierPathWithColorChange(car, false, goalPoint);
    totalDashedLength = drawDashedBezierPathWithOffset(car, car.position, goalPoint, 15, 10, 5, 2);
  }
  
  return totalDashedLength; // 전체 경로 길이 반환
}


function navigateToGoal(car, goalX, goalY, speedIncrement) {
  
  // 목표 지점 설정
  const goalPoint = { 
    x: goalX, 
    y: goalY 
  };

  // 최종 목표 지점을 유지
  car.initialGoalX = car.initialGoalX || goalPoint.x;

  // 복구 지점 없이 목표 지점으로 바로 이동
  drawBezierPath(car, false, goalPoint);

  // 차량이 최종 목표를 향해 바로 이동
  const dxToGoal = goalPoint.x - car.position.x;
  const dyToGoal = goalPoint.y - car.position.y;
  const distanceToGoal = Math.sqrt(dxToGoal * dxToGoal + dyToGoal * dyToGoal);

  // 방향 계산
  const desiredDirection = Math.atan2(dyToGoal, dxToGoal);

  car.direction = normalizeDirection(desiredDirection);

  // 차량 위치 업데이트
  car.speed = speedIncrement; // 속도는 최대 5로 제한
  car.position.x += car.speed * Math.cos(car.direction);
  car.position.y += car.speed * Math.sin(car.direction);
}

/**
 * 가장 가까운 차선 복귀 지점을 찾음
 * @param {Object} car - 차량 데이터
 * @param {Array} laneBoundsX - 차선 경계
 * @param {number} goalY - 목표 Y 좌표
 * @returns {Object} 복귀 지점 좌표
 */
function findClosestLanePoint(car, laneBoundsX, goalY, boundx = 2) {
  const currentX = car.position.x;

  // 차선 범위를 벗어난 경우, 가장 가까운 차선 경계점 반환
  if (currentX < laneBoundsX[0] || currentX > laneBoundsX[1]) {
    const closestX = currentX < laneBoundsX[0] ? laneBoundsX[0] : laneBoundsX[1];
    return { x: closestX, y: goalY }; // y축을 goalY로 설정하여 더 부드러운 복귀 유도
  }

  // 차선 범위 내에 있는 경우, 목표 경로의 중앙으로 이동
  return { x: (laneBoundsX[0] + laneBoundsX[1]) / boundx, y: goalY }; 
}

function displayGauges(bit_max_nb = 0, bit_min_nb = 0) {
  const gaugeX = width - 600; // 텍스트가 표시될 X 위치
  const gaugeSpacing = 30; // 텍스트 간 간격
  const startY = 60; // 텍스트 표시 시작 Y 위치
  
  // 박스 배경 추가 (테두리 없이 완전 투명한 박스)
  noStroke(); // 테두리 제거
  //fill(0, 0, 0, 150); // 반투명 검은색 (투명도 조정)
  //rect(gaugeX - 10, 50, 250, 900); // 박스 크기 조정

  // 텍스트 설정 (그림자 없음)
  fill(0, 0, 0, 256); // 검은색(0, 0, 0) + 투명도(128: 반투명)
  textSize(16);
  textStyle(NORMAL); // 굵기 기본값
  textAlign(LEFT, CENTER); // 왼쪽 정렬
  
  //let segmentLengths = []; // 각 점선 구간의 길이를 저장
  //let segmentAngles = [];  // 각 점선 구간의 각도를 저장
  
  
  // 텍스트 라벨 및 값 설정
  const gauges = [
    { label: "자동 주행 테스트는 스페이스를 누르세요.", value: ''},
    { label: "IndexDB 이름", value: indexDBName },
    { label: "IndexDB 모델", value: indexDBModel },
    { label: "자동 주행 상태", value: trainingMode},
    { label: "학습 상태", value: indexConsole},
    { label: "N/B 예측 속도", value: Number($('.nb-dependency-speed').text()).toFixed('15') },
    { label: "N/B 예측 조향", value: Number($('.nb-dependency-direction').text()).toFixed('5') },
    { label: "ML 예측 속도", value: Number($('.machine-learning-speed').text()).toFixed('15') },
    { label: "ML 예측 조향", value: Number($('.machine-learning-direction').text()).toFixed('5') },
    { label: "AI 추론 패널티 증가 확률", value: Number($('.penalty-increase-probability').text()).toFixed(5) },
    { label: "AI 추론 N/B 증가 확률", value: Number($('.nb-increase-probability').text()).toFixed(5) },
    { label: "AI 추론의 방향", value: indexangleDifference },
    { label: "AI 추론 경로 길이", value: indexLine},
    { label: "AI 추론 길이 학습 MAX N/B", value: segmentLengthsBitMax },
    { label: "AI 추론 길이 학습 MIN N/B", value: segmentLengthsBitMin },
    { label: "AI 추론 각도 학습 MAX N/B", value: segmentAnglesBitMax },
    { label: "AI 추론 각도 학습 MIN N/B", value: segmentAnglesBitMin },
    { label: "조향 회전률 MAX N/B", value: bit_max_nb },
    { label: "조향 회전률 MIN N/B", value: bit_min_nb },
    { label: "브레이크 상태", value: primaryCarData[2] || 0 },
    { label: "브레이크 압력", value: primaryCarData[3] || 0 },
    //{ label: "엔진 출력", value: primaryCarData[4] || 0 },
    //{ label: "타이어 상태", value: primaryCarData[5] || 0 },
    //{ label: "안정성 제어", value: primaryCarData[6] || 0 },
    //{ label: "트랙션 제어", value: primaryCarData[7] || 0 },
    //{ label: "연료 상태", value: primaryCarData[8] || 0 },
    //{ label: "가속도 X", value: primaryCarData[9] || 0 },
    //{ label: "가속도 Y", value: primaryCarData[10] || 0 },
    { label: "도로 속도 변화", value: roadSpeed},
  ];

  // 텍스트만 표시
  for (let i = 0; i < gauges.length; i++) {
    const gauge = gauges[i];
    const y = startY + i * gaugeSpacing;
    if(i < 12) {
      text(`${gauge.label}: ${gauge.value}`, gaugeX, y);
    } else {
      text(`${gauge.label}: ${gauge.value.toFixed(5)}`, gaugeX, y);
    }
  }
}

/**
 * 차량 이동 처리
 */
function moveCar(primaryCar, goalX, goalY, maxSpeed = 5) {
  // 현재 위치와 목표 지점 간의 거리 계산
  const dx = goalX - primaryCar.position.x;
  const dy = goalY - primaryCar.position.y;
  const distanceToGoal = Math.sqrt(dx * dx + dy * dy);

  // 목표 방향 계산
  const desiredDirection = Math.atan2(dy, dx);

  // 방향 부드럽게 전환
  const blendingFactor = 0.1;
  classDirection = classDirection * (1 - blendingFactor) + desiredDirection * blendingFactor;

  // 속도 설정
  const speed = Math.min(maxSpeed, distanceToGoal); // 목표 지점 근처에서는 속도 감소

  // 차량 위치 업데이트
  primaryCar.position.x += speed * Math.cos(classDirection);
  primaryCar.position.y += speed * Math.sin(classDirection);

  // 콘솔 출력으로 확인
  //console.log(`Car Position: (${primaryCar.position.x}, ${primaryCar.position.y}), Direction: ${classDirection}`);
}


/**
 * 차량의 위치를 업데이트
 * @param {Object} car - 차량 데이터
 * @param {number} direction - 이동 방향
 * @param {number} speed - 이동 속도
 * @param {number} front - 정면 거리
 */
function updateCarPosition(car, direction, speed, front) {
  const maxSteeringAngle = PI / 6; // 최대 핸들링 각도 (30도)
  const acceleration = 0.1; // 가속도
  const maxSpeed = 5; // 최대 속도
  const steeringSpeed = 0.02; // 조향 각도 변경 속도
    
  
    car.speed = speed; // 가속
    
    car.direction = direction; // 왼쪽으로 조향
  
    // 방향 유지하며 이동
    primaryCar.position.x += cos(primaryCar.direction) * car.speed;
    primaryCar.position.y += sin(primaryCar.direction) * car.speed;
  
    // 방향 정규화 (-PI ~ PI 범위 유지)
    car.direction = normalizeDirection(direction);
  
  if (keyIsDown(DOWN_ARROW)) {
    car.speed = (car.speed) - (car.speed + 1); // 후진
    
    // 방향 유지하며 이동
    primaryCar.position.x += cos(primaryCar.direction) * car.speed;
    primaryCar.position.y += sin(primaryCar.direction) * car.speed;
  } else {
    // 마찰 효과로 인해 속도가 점진적으로 감소
    car.speed *= 0.95;
    if (Math.abs(car.speed) < 0.01) car.speed = 0; // 정지 상태
  }

  // 조향 제어 (좌/우 방향키)
  if (keyIsDown(LEFT_ARROW)) {
    car.direction -= steeringSpeed; // 왼쪽으로 조향
  }
  if (keyIsDown(RIGHT_ARROW)) {
    car.direction += steeringSpeed; // 오른쪽으로 조향
  }

  // 방향 정규화 (-PI ~ PI 범위 유지)
  car.direction = normalizeDirection(car.direction);
}

/**
 * 키보드 입력 처리
 * @param {Object} car - 차량 데이터
 */
function handleKeyboardInput(car) {
  const maxSteeringAngle = PI / 6; // 최대 핸들링 각도 (30도)
  const acceleration = 0.1; // 가속도
  const maxSpeed = 5; // 최대 속도
  const steeringSpeed = 0.02; // 조향 각도 변경 속도
  
  let isKeyPressed = false; // 키 입력 상태 확인 변수

  // 속도 제어 (위/아래 방향키)
  if (keyIsDown(UP_ARROW)) {
    car.speed = Math.min(car.speed + acceleration, maxSpeed); // 가속
    
    // 방향 유지하며 이동
    primaryCar.position.x += cos(primaryCar.direction) * car.speed;
    primaryCar.position.y += sin(primaryCar.direction) * car.speed;
    isKeyPressed = true; // 키 입력 상태 업데이트
    contRoler = true;
  } else if (keyIsDown(DOWN_ARROW)) {
    car.speed = Math.max(car.speed - acceleration * 2, -maxSpeed); // 후진 속도 증가
    
    // 방향 유지하며 이동
    primaryCar.position.x += cos(primaryCar.direction) * car.speed;
    primaryCar.position.y += sin(primaryCar.direction) * car.speed;
    isKeyPressed = true; // 키 입력 상태 업데이트
    contRoler = true;
  } else {
    // 마찰 효과로 인해 속도가 점진적으로 감소
    car.speed *= 0.95;
    if (Math.abs(car.speed) < 0.01) car.speed = 0; // 정지 상태
  }

  // 조향 제어 (좌/우 방향키)
  if (keyIsDown(LEFT_ARROW)) {
    car.direction -= steeringSpeed; // 왼쪽으로 조향
    isKeyPressed = true; // 키 입력 상태 업데이트
    contRoler = true;
  }
  if (keyIsDown(RIGHT_ARROW)) {
    car.direction += steeringSpeed; // 오른쪽으로 조향
    isKeyPressed = true; // 키 입력 상태 업데이트
    contRoler = true;
  }

  // 키가 눌리지 않은 경우
  if (!isKeyPressed) {
    //console.log("키가 눌리지 않았습니다. 차량은 현재 상태를 유지합니다.");
    // 원하는 동작 수행 (예: 속도 감속, 상태 변경 등)
    car.speed *= 0.9; // 속도 완만한 감소
    isKeyPressed = false; // 키 입력 상태 업데이트
    contRoler = false;
  }

  // 방향 정규화 (-PI ~ PI 범위 유지)
  car.direction = normalizeDirection(car.direction);
}

// 패널티 및 보상 계산

/**
 * 차량 페널티 점수 계산
 * @param {Object} primaryCar - 차량 데이터
 * @param {Object} distances - 센서 거리 데이터
 * @param {number} divisor - 페널티 계산 기준값
 */
function calculatePenalty(primaryCar, distances, divisor = 1000) {
  // 거리 값을 1000으로 나눈 후 페널티에 추가
  const penalty = 
    (distances.front / divisor) + 
    (distances.back / divisor) + 
    (distances.right / divisor) + 
    (distances.left / divisor);

  // 차량의 페널티 점수 업데이트
  //primaryCar.penaltyPoints += penalty;
}

/**
 * 차량 보상 및 추가 패널티 점수 계산
 * @param {Object} primaryCar - 차량 데이터
 * @param {number} adjustmentFactor - 조정 값
 */
function calculatePenaltyAndReward(primaryCar, adjustmentFactor = 1) {
  let ps = primaryCar.speed;
  const directionValue = primaryCar.direction; // 방향 값 (라디안)

  // 기본 패널티와 보상 값 계산
  let penaltyPoints = 0;

  // 속도가 낮거나 음수(후진)일 경우
  if (ps < 0) { 
    //penaltyPoints += Math.min(10, Math.abs(ps) + 2) * adjustmentFactor; 
  } else if (ps < 2) { 
    //penaltyPoints += Math.min(10, (2 - ps) + 2) * adjustmentFactor;
  } else if (ps > 4) {
    //penaltyPoints -= Math.max(0, Math.min(10, (ps - 4) + 2)) * adjustmentFactor;
  }

  // 조향 데이터 기반 보상 및 패널티
  if (BIT_MAX_NB(steeringSpeed) > BIT_MIN_NB(steeringSpeed)) {
    penaltyPoints -= Math.max(0, Math.min(10, ps + 3)) * adjustmentFactor;
  } else if (
    BIT_MAX_NB(steeringSpeed) < 0 && 
    BIT_MIN_NB(steeringSpeed) < 0 && 
    BIT_MAX_NB(steeringSpeed) < BIT_MIN_NB(steeringSpeed)
  ) {
    penaltyPoints += Math.min(10, Math.abs(ps) + 3) * adjustmentFactor;
  }

  // 방향 기반 보상 및 패널티
  if (directionValue > Math.PI / 4 && directionValue < (3 * Math.PI) / 4) {
    //primaryCar.penaltyPoints += penaltyPoints;
    console.log("보상: 차량이 위쪽으로 향하고 있습니다.");
  } else if (directionValue > -Math.PI / 4 && directionValue < Math.PI / 4) {
    //penaltyPoints -= Math.max(0, Math.min(10, 2)) * adjustmentFactor;
    //primaryCar.penaltyPoints += penaltyPoints;
  } else if (directionValue > (3 * Math.PI) / 4 || directionValue < -(3 * Math.PI) / 4) {
    
    //primaryCar.penaltyPoints -= penaltyPoints;
    console.log("패널티: 차량이 아래쪽으로 향하고 있습니다.");
  }

}

// =====================================
// 4. UI 및 시각화 관련
// =====================================

// 차량 및 도로 시각화

/**
 * 도로와 차량, UI 등을 그리는 메인 함수
 */
let boundx = 0;
function draw() {
  background(220);
    // 콘솔창에 로그 추가
  logToConsole(`Car Position: (${primaryCar.position.x.toFixed(2)}, ${primaryCar.position.y.toFixed(2)})`);
  // 방향키 입력 처리
  //handleKeyboardInput(primaryCar);
  
  // 차량 상태 업데이트 (학습 활성화 시에만)
  if (isTraining || getAllURLParameters()) {
      primaryCar.bit_max_nb = 0;  
      primaryCar.bit_min_nb = 0;
    
      segmentLengthsBitMax = BIT_MAX_NB(segmentLengths); // segmentLengths의 최대값 저장
      segmentLengthsBitMin = BIT_MIN_NB(segmentLengths); // segmentLengths의 최소값 저장

      segmentAnglesBitMax = BIT_MAX_NB(segmentAngles); // segmentAngles의 최대값 저장
      segmentAnglesBitMin = BIT_MIN_NB(segmentAngles); // segmentAngles의 최소값 저장
      
      primaryCar.bit_max_nb += segmentLengthsBitMax;
      primaryCar.bit_min_nb += segmentAnglesBitMin;
    
      primaryCar.bit_max_nb += segmentAnglesBitMax;
      primaryCar.bit_min_nb += segmentAnglesBitMin;
    
      //primaryCar.penaltyPoints += ((segmentLengthsBitMax + segmentAnglesBitMin) / 100)
    
      // 차량이 차선에서 벗어났는지 확인
      let isOutOfLane = updateCarState(calculateSensorDistances(primaryCar), 0.01)
      
      const distances = calculateSensorDistances(primaryCar, isOutOfLane);
    
      let ps = primaryCar.speed;

      // 기본 페널티 계산
      //calculatePenalty(primaryCar, distances, 10000); // 페널티 계산 및 업데이트

      //calculatePenaltyAndReward(primaryCar, 0.005); // 절반 크기의 보상/패널티
    
      push();
      translate(primaryCar.position.x, primaryCar.position.y);
      rotate(primaryCar.direction);
      //drawSensors(primaryCar, distances);
      pop();

      updatePrimaryCarData();
      handleKeyboardInput(primaryCar);
    
    
      if (saveCooldown <= 0) {
        // 유사한 차량 시뮬레이션 데이터를 검색 //false 가장 낮은 패널티, true 가장 높은 패널티
        getSimilarCarSimulationData("primaryCar", primaryCar.bit_max_nb, primaryCar.bit_min_nb, 5, false)
          .then((result) => {
          console.log("getSimilarCarSimulationData:", result);
          
          // 중복 데이터가 아니고 차량 속도가 0이 아닌 경우에만 데이터 저장
          if (!result.isDuplicate) {
            Promise.all([
              saveCarSimulationData({
                type: "primaryCarData",
                data: primaryCarData,
              }),
              saveCarSimulationData({
                type: "primaryCar",
                data: primaryCar,
              }),
            ]).catch((error) => {
              console.error("데이터 저장 중 오류 발생:", error);
            });
          } else {
            console.log("중복된 데이터가 있습니다.");
          }

          if (result.data.length > 0) {
            
            // IndexedDB에서 검색된 데이터가 존재하는지 확인합니다.
            // `result.data` 배열의 길이가 0보다 크면 데이터를 처리합니다.

            // IndexedDB에서 검색된 데이터가 존재하는지 확인합니다.
            // `result.data` 배열의 길이가 0보다 크면 데이터를 처리합니다.
            let highPenaltyData = result.data.map(item => ({
                bit_max_nb: item.bit_max_nb, // 검색된 데이터에서 최대 비트 값을 가져옵니다.
                bit_min_nb: item.bit_min_nb, // 검색된 데이터에서 최소 비트 값을 가져옵니다.
                penaltyPoints: item.penaltyPoints, // 검색된 데이터에서 페널티 점수를 가져옵니다.
                bitIncreaseProbability: result.probabilities.bitIncreaseProbability, // 비트 증가 확률을 가져옵니다.
                penaltyIncreaseProbability: result.probabilities.penaltyIncreaseProbability, // 페널티 증가 확률을 가져옵니다.
            }));

            // 현재 차량 데이터를 구성합니다.
            const currentCarData = {
                bit_max_nb: primaryCar.bit_max_nb, // 현재 차량의 최대 비트 값 (bit_max_nb)
                bit_min_nb: primaryCar.bit_min_nb, // 현재 차량의 최소 비트 값 (bit_min_nb)
                speed: primaryCar.speed,           // 현재 차량의 속도
                direction: primaryCar.direction,   // 현재 차량의 방향
                bitIncreaseProbability: result.probabilities.bitIncreaseProbability, // 비트 증가 확률
                penaltyIncreaseProbability: result.probabilities.penaltyIncreaseProbability, // 페널티 증가 확률
            };

            // 검색된 데이터와 현재 차량 데이터를 디버깅용으로 출력
            //console.log("High Penalty Data:", highPenaltyData); // 검색된 높은 페널티 데이터 출력
            console.log("Current Car Data:", currentCarData);   // 현재 차량 데이터 출력

            if (segmentLengthsBitMax === 0.055 && segmentLengthsBitMin === 0.055 && segmentAnglesBitMax === 0.055 && segmentAnglesBitMin === 0.055) {
                if(primaryCar.penaltyPoints === 0) {
                  indexConsole = 'N/B 의존성 학습이 안정적으로 재시작 됩니다.';
                  indexState = true;
                } else if (primaryCar.penaltyPoints < 0.0005) {
                  indexConsole = '현재 차량이 정지 상태입니다. 포인트가 초기화 됩니다.';
                  indexState = false;
                  boundx = Math.random() < 0.5 ? 2 : 2.5;
                } else if (segmentLengthsBitMax > 0.1 || segmentAnglesBitMax > 0.1) {
                  indexConsole = 'N/B 의존성 학습이 활성화되었습니다. 현재 데이터가 충분히 수집되고 있습니다.';

                  indexState = true;
                } else if (segmentLengthsBitMax < 0.01 && segmentAnglesBitMax < 0.01) {
                  indexConsole = '학습 데이터가 부족합니다. 데이터 수집을 확인하세요.';

                  indexState = true;
                }
              } else {
                trainModelWithSpeed(highPenaltyData, currentCarData);
                indexConsole = '현재 N/B 의존성 학습이 진행 중입니다. 결과를 모니터링하세요.';

                indexState = true;
              }
            // URL 매개변수가 존재하면 처리
            if (getAllURLParameters()) {
              if (result.data.length > 1) {
                // 모델에 입력 데이터를 예측
                predictLowestPenaltyBasedOnBits(currentCarData).then((predictionResult) => {
                  console.log("예측 결과:", predictionResult);
                    $('.machine-learning-speed').text(predictionResult.car.speed);
                    $('.machine-learning-direction').text(predictionResult.car.direction);
                  // 모델을 IndexedDB에 저장
                  saveModelToIndexedDB(model);
                });
                  if(result.data[0].type === "primaryCar") {
                    $('.nb-dependency-speed').text(result.data[0].data.speed);
                    $('.nb-dependency-direction').text(result.data[0].data.direction);
                  }
                  if(result.data[0].type === "primaryCarData") {
                    $('.nb-dependency-speed').text(result.data[0].data.vehicleStatus.speed);
                    $('.nb-dependency-direction').text(result.data[0].data.vehicleStatus.direction);
                  }
              }
            } else {
              
                if(result.data[0].type === "primaryCar") {
                  $('.nb-dependency-speed').text(result.data[0].data.speed);
                  $('.nb-dependency-direction').text(result.data[0].data.direction);
                }
                if(result.data[0].type === "primaryCarData") {
                  $('.nb-dependency-speed').text(result.data[0].data.vehicleStatus.speed);
                  $('.nb-dependency-direction').text(result.data[0].data.vehicleStatus.direction);
                }
                // 모델에 입력 데이터를 예측
                predictLowestPenaltyBasedOnBits(currentCarData).then((predictionResult) => {
                  console.log("예측 결과:", predictionResult);
                  if(result.data[0].type === "primaryCar") {
                    $('.nb-dependency-speed').text(result.data[0].data.speed);
                    $('.nb-dependency-direction').text(result.data[0].data.direction);
                  }
                  if(result.data[0].type === "primaryCarData") {
                    $('.nb-dependency-speed').text(result.data[0].data.vehicleStatus.speed);
                    $('.nb-dependency-direction').text(result.data[0].data.vehicleStatus.direction);
                  }

                  $('.machine-learning-speed').text(predictionResult.car.speed);
                  $('.machine-learning-direction').text(predictionResult.car.direction);
                  
                  $('.penalty-increase-probability').text(predictionResult.car.penaltyIncreaseProbability);
                  $('.nb-increase-probability').text(predictionResult.car.bitIncreaseProbability);
                  
                  // 모델을 IndexedDB에 저장
                  saveModelToIndexedDB(model);
                });
            }

            // 방향 데이터를 배열에 추가
            steeringSpeed.push(Number($('.nb-dependency-direction').text()));
            
            // 배열 길이가 255를 초과하면 가장 오래된 값 제거
            if (steeringSpeed.length > 255) {
              steeringSpeed.shift();
            }
          }
        })
          .catch((error) => {
          console.error("데이터 검색 중 오류 발생:", error);
        });

        // 저장 쿨다운 설정 (1 프레임 대기)
        saveCooldown = 10;
      } else {
        // 저장 쿨다운 감소
        saveCooldown--;
      }

  }

    // 직선 도로 그리기
    drawStraightRoad();

    // 우측 게이지 표시
    displayGauges(BIT_MAX_NB(steeringSpeed), BIT_MIN_NB(steeringSpeed));
  
    // 좌측 차량 데이터 출력
    displayCarData();
  
    displayWarningIfCarOut(primaryCar);
    // 경계선 그리기
    //drawBoundingBox();
    updateSensorData(primaryCar)
  
    drawBoundingBox();

    //console.log("steeringSpeed BIT MAX N/B", BIT_MAX_NB(steeringSpeed));
    //console.log("steeringSpeed BIT MIN N/B", BIT_MIN_NB(steeringSpeed));
    //createTreasure()
  
    drawPrimaryCar____(newCar);
  
    // 단일 차량 그리기
    drawPrimaryCar(primaryCar, newCar);
  
}

/**
 * 차량을 시각적으로 화면에 표시
 * @param {Object} car - 차량 데이터
 */
function drawPrimaryCar____(car) {
  push();
  translate(car.position.x, car.position.y);
  rotate(car.direction);

  // 차량 본체 색상 설정
  if (isTraining) {
    fill(123, 104, 238); // 학습 중: 미디엄 슬레이트 블루
  } else if (car.speed > 8) {
    fill(75, 0, 130); // 속도가 빠를 때: 인디고
  } else if (car.penaltyPoints < -5) {
    fill(255, 105, 180); // 패널티 점수 매우 낮을 때: 핫핑크
  } else {
    fill(0, 255, 255); // 기본 상태: 시안
  }

  rectMode(CENTER);
  rect(0, 0, 60, 30, 10); // 둥근 모서리(10)

  // 타이어
  fill(43, 43, 43); // 검정색
  rect(-25, -10, 10, 8); // 왼쪽 앞 타이어
  rect(25, -10, 10, 8);  // 오른쪽 앞 타이어
  rect(-25, 10, 10, 8);  // 왼쪽 뒤 타이어
  rect(25, 10, 10, 8);   // 오른쪽 뒤 타이어

  // 유리창
  fill(173, 216, 230); // 연한 파란색
  rect(0, -5, 40, 10); // 전면 유리창
  fill(12, 93, 148); // 어두운 파란색
  rect(0, 5, 40, 10); // 후면 유리창

  // 중앙 스트라이프
  fill(255, 255, 0); // 노란색
  rect(-5, 0, 5, 30); // 왼쪽 스트라이프
  rect(5, 0, 5, 30);  // 오른쪽 스트라이프

  // 전조등
  fill(255, 255, 0); // 노란색
  ellipse(30, -8, 5, 5); // 왼쪽 전조등
  ellipse(30, 8, 5, 5);  // 오른쪽 전조등

  // 후미등
  fill(255, 0, 0); // 빨간색
  ellipse(-30, -8, 5, 5); // 왼쪽 후미등
  ellipse(-30, 8, 5, 5);  // 오른쪽 후미등

  pop();

  // 센서 그리기
  const distances = calculateSensorDistances(car); // 센서 거리 계산
  drawSensors(car, distances); // 센서 시각화
  if(isTraining === true && indexState === true) {

    if(trainingMode === false) {

    } else {
      //let boundx = Math.random() < 0.5 ? 2 : 2.5;
      // Lane boundaries for the second lane
      const laneBoundsX = [(width / 2) - 50, (width / 2) + 50]; // 왼쪽으로 50px, 오른쪽으로 50px
      const goalY = 50; // Topmost coordinate of the second lane

      //indexLine = navigateToGoal(primaryCar, laneBoundsX, goalY);
      const classSpeed = Number($('.nb-dependency-speed').text()) - 1
      const classDirection = Number($('.nb-dependency-direction').text())
      let goalX = laneBoundsX[boundx];

      if(newCar.position.y > height - 50) {

        boundx =  Math.random() < 0.5 ? 0 : 1; //좌, 우 도로

        goalX = laneBoundsX[boundx];
        newCar.position.x = goalX; 
        newCar.position.y = 100;

        indexLine = navigateToGoal(newCar, goalX, goalY, classSpeed);
      } else {
        indexLine = navigateToGoal(newCar, goalX, goalY, classSpeed);
      }
    }
  }
}

/**
 * 차량의 목표 지점까지의 경로를 선으로 그리기
 * @param {Object} car - 차량 데이터
 * @param {Object} target - 목표 좌표
 */
function drawPathLine(car, target) {
  stroke(0, 0, 0); // 선의 색상: 녹색
  strokeWeight(2); // 선의 두께
  line(car.position.x, car.position.y, target.x, target.y); // 차량 위치에서 목표 위치까지 선 그리기
}

/**
 * 차량 경로를 곡선으로 시각화
 * @param {Object} car - 차량 데이터
 * @param {Object} recoveryPoint - 복귀 지점
 * @param {Object} goalPoint - 목표 지점
 */
/**
 * 차량의 위치에서 목표 지점까지 곡선 경로를 그립니다.
 * 복구 지점(recoveryPoint)을 사용할지 여부를 자동 처리합니다.
 *
 * @param {Object} car - 차량 객체 (현재 위치 포함).
 * @param {Object|null} recoveryPoint - 복구 지점의 좌표 {x, y} (없을 경우 null).
 * @param {Object} goalPoint - 최종 목표 지점의 좌표 {x, y}.
 */
function drawBezierPath(car, recoveryPoint, goalPoint) {
  stroke(128, 128, 128, 150); // 곡선 색상: 투명한 회색
  strokeWeight(15); // 곡선 두께
  // noFill(); // 내부를 채우지 않음

  beginShape(); // 곡선 그리기 시작

  // 시작점: 차량의 현재 위치
  vertex(car.position.x, car.position.y);

  if (recoveryPoint !== false) {
    // 복구 지점이 있는 경우: 복구 지점 → 목표 지점으로 곡선을 연결
    quadraticVertex(
      recoveryPoint.x, recoveryPoint.y, // 제어점: 복구 지점
      goalPoint.x, goalPoint.y // 끝점: 목표 지점
    );
  } else {
    // 복구 지점이 없는 경우: 차량과 목표 지점의 중간점을 사용하여 자연스러운 곡선 생성
    const midX = (car.position.x + goalPoint.x) / 2; // 차량과 목표 지점의 중간 X 좌표
    const midY = (car.position.y + goalPoint.y) / 2; // 차량과 목표 지점의 중간 Y 좌표

    quadraticVertex(
      midX, midY, // 제어점: 중간 지점
      goalPoint.x, goalPoint.y // 끝점: 목표 지점
    );
  }

  endShape(); // 곡선 그리기 종료
}

/**
 * 차량의 위치에서 목표 지점까지 곡선 경로를 그립니다.
 * 차량(newCar)이 경로에 닿으면 곡선 색상이 주황색으로 변경됩니다.
 *
 * @param {Object} car - 차량 객체 (현재 위치 포함).
 * @param {Object|boolean} recoveryPoint - 복구 지점의 좌표 {x, y} (없을 경우 false).
 * @param {Object} goalPoint - 최종 목표 지점의 좌표 {x, y}.
 * @param {Object} newCar - 추가 차량 객체 (닿음 여부를 확인하기 위한 위치 포함).
 */
 let collisionDetected = false; // 충돌 여부 초기화
function drawBezierPathWithColorChange(car, recoveryPoint, goalPoint) {
 
  // 곡선 기본 색상
  let baseStrokeColor = color(128, 128, 128, 150); // 투명한 회색

  beginShape(); // 곡선 그리기 시작

  // 시작점: 차량의 현재 위치
  vertex(car.position.x, car.position.y);

  if (recoveryPoint !== false) {
    // 복구 지점이 있는 경우: 복구 지점 → 목표 지점으로 곡선을 연결
    quadraticVertex(
      recoveryPoint.x, recoveryPoint.y, // 제어점: 복구 지점
      goalPoint.x, goalPoint.y // 끝점: 목표 지점
    );

    // 충돌 여부 확인
    collisionDetected = checkCollisionWithBezier(
      car.position, recoveryPoint, goalPoint, newCar
    );
  } else {
    // 복구 지점이 없는 경우: 차량과 목표 지점의 중간점을 사용하여 자연스러운 곡선 생성
    const midX = (car.position.x + goalPoint.x) / 2; // 차량과 목표 지점의 중간 X 좌표
    const midY = (car.position.y + goalPoint.y) / 2; // 차량과 목표 지점의 중간 Y 좌표

    quadraticVertex(
      midX, midY, // 제어점: 중간 지점
      goalPoint.x, goalPoint.y // 끝점: 목표 지점
    );

    // 충돌 여부 확인
    collisionDetected = checkCollisionWithBezier(
      car.position, { x: midX, y: midY }, goalPoint, newCar
    );
  }
  
  // 색상 변경
  if (collisionDetected) {
    stroke(255, 165, 0, 150); // 충돌 시 색상: 투명한 주황색
    console.log("충돌 발생!");
    strokeWeight(25); // 두께 유지
  } else {
    stroke(baseStrokeColor); // 기본 색상 유지
    //console.log("충돌 없음.");
    strokeWeight(15); // 두께 유지
  }

  endShape(); // 곡선 그리기 종료

}

// 충돌 확인 함수: 곡선과 newCar 간 거리 계산
function checkCollisionWithBezier(start, control, end, newCar) {
  for (let t = 0; t <= 1; t += 0.01) {
    const x = bezierPoint(start.x, control.x, control.x, end.x, t);
    const y = bezierPoint(start.y, control.y, control.y, end.y, t);

    const dx = newCar.position.x - x;
    const dy = newCar.position.y - y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance < 20) {
      // 충돌 거리 조건 (20px 이내)
      return true;
    }
  }
  return false;
}


/**
 * Bezier 곡선 점선 경로를 차량 앞에서부터 그리며, 점선 개수와 두께를 조정 가능.
 *
 * @param {Object} car - 차량 객체 (현재 위치 및 방향 포함).
 * @param {Object} recoveryPoint - 복귀 지점의 좌표 {x, y}.
 * @param {Object} goalPoint - 최종 목표 지점의 좌표 {x, y}.
 * @param {number} dashLength - 점선의 길이 (기본값: 10).
 * @param {number} gapLength - 점선 사이의 간격 (기본값: 5).
 * @param {number} thickness - 점선의 두께 (기본값: 2).
 * @param {number} offsetDistance - 차량 전면과 시작 지점 사이의 거리 (기본값: 30).
 * @param {number} minSteps - 점선의 최소 개수 (기본값: 2).
 * @param {number} maxSteps - 점선의 최대 개수 (기본값: 20).
 * @returns {number} - 전체 점선 경로의 총 길이.
 */
let dashedSegments = [];
let dashedCenters = []; // 새로운 배열: 점선 중심 좌표만 저장
function drawDashedBezierPathWithOffset(
  car, 
  recoveryPoint, 
  goalPoint, 
  dashLength = 10, 
  gapLength = 5, 
  thickness = 2, 
  offsetDistance = 30, 
  minSteps = 2, 
  maxSteps = 10
) {
  strokeWeight(thickness); // 점선 두께 설정

  // 차량의 전면에서 시작점 계산 (offsetDistance만큼 떨어진 위치)
  const startX = car.position.x + Math.cos(car.direction) * offsetDistance;
  const startY = car.position.y + Math.sin(car.direction) * offsetDistance;

  // 전체 경로 길이를 계산
  const totalLength = dist(startX, startY, recoveryPoint.x, recoveryPoint.y) + 
                      dist(recoveryPoint.x, recoveryPoint.y, goalPoint.x, goalPoint.y);

  // 점선 개수 설정 (길이가 짧을수록 steps가 줄어듦)
  const steps = Math.max(minSteps, Math.min(maxSteps, Math.floor(totalLength / 50))); // 길이에 따라 조정

  let totalDashedLength = 0;
  
  segmentLengths = [];
  segmentAngles = [];

  for (let i = 0; i < steps; i++) {
    const tStart = i / steps; // 시작 비율
    const tEnd = (i + 0.5) / steps; // 끝 비율 (점선 끝)

    // 시작 점 계산 (Bezier 공식, 차량 전면에서 시작)
    const x1 = bezierPoint(startX, recoveryPoint.x, recoveryPoint.x, goalPoint.x, tStart);
    const y1 = bezierPoint(startY, recoveryPoint.y, recoveryPoint.y, goalPoint.y, tStart);

    // 끝 점 계산 (Bezier 공식)
    const x2 = bezierPoint(startX, recoveryPoint.x, recoveryPoint.x, goalPoint.x, tEnd);
    const y2 = bezierPoint(startY, recoveryPoint.y, recoveryPoint.y, goalPoint.y, tEnd);

    // 점선의 길이 계산
    const segmentLength = dist(x1, y1, x2, y2);
    segmentLengths.push(segmentLength); // 길이 배열에 추가
    totalDashedLength += segmentLength; // 총 점선 길이 누적

    // 점선의 각도 계산
    const angle = atan2(y2 - y1, x2 - x1); // 라디안 값
    segmentAngles.push(degrees(angle)); // 각도 배열에 추가 (도 단위로 변환)
    
    // 점선 중심 좌표 계산
    const centerX = (x1 + x2) / 2; // 중심 x 좌표
    const centerY = (y1 + y2) / 2; // 중심 y 좌표

    // 점선 데이터 저장
    dashedCenters.push({ x: centerX, y: centerY }); // 중심 좌표만 저장
    
    // 점선 정보 저장
    dashedSegments.push({ x1, y1, x2, y2, angle });
    
    // 투명도 조정: 점진적으로 줄어드는 투명도 설정
    const alpha = map(i, 0, steps, 150, 50); // 처음은 150, 끝은 50
    stroke(0, 255, 255, alpha);

    // 점선 그리기
    line(x1, y1, x2, y2);
  }
  // 전체 경로 길이 반환
  return totalDashedLength;
}


/**
 * 직선 도로를 화면에 그리기
 */
let roadOffset = 0; // 도로 스크롤 위치
let roadSpeed = 0; // 도로가 움직이는 속도

function drawStraightRoad() {
  const roadWidth = 200; // 도로 폭
  const laneWidth = roadWidth / 2; // 차선 폭
  const leftLaneColor = '#A9A9A9'; // 왼쪽 차선 색상
  const rightLaneColor = '#696969'; // 오른쪽 차선 색상
  const laneColor = '#EEE'; // 점선 색상
  const centerX = width / 2;

  let targetY = height - 300; // primaryCar가 이동하려는 목표 y 위치
  
  // 도로 전체 배경
  noStroke();
  fill('#808080'); // 도로 배경색
  rect(centerX - roadWidth / 2, 0, roadWidth, height);

  // 왼쪽 차선
  fill(leftLaneColor);
  rect(centerX - laneWidth, 0, laneWidth, height);

  // 오른쪽 차선
  fill(rightLaneColor);
  rect(centerX, 0, laneWidth, height);

  // 점선 그리기
  stroke(laneColor);
  strokeWeight(4);
  let y = roadOffset % 40; // 점선의 초기 위치를 계산
  
  while (y < height) {
    line(centerX, y, centerX, y + 20); // 점선 그리기
    y += 40; // 다음 점선 위치
  }

  if(isTraining) {
    
    // 도로 스크롤 효과
    roadOffset += roadSpeed;
    if (roadOffset >= 40) {
      roadOffset = 0; // 반복되도록 초기화
  }


    // roadSpeed를 primaryCar가 목표 y 위치에 맞게 조절 (물리적 효과 적용)
    const acceleration = 0.2; // 가속도
    const maxSpeed = 6; // 최대 속도
    const minSpeed = 1; // 최소 속도
    let currentSpeed = roadSpeed; // 현재 속도

    if (primaryCar.position.y < targetY) {
      // 아래로 이동
      currentSpeed += acceleration; // 가속
      roadSpeed = Math.min(currentSpeed, maxSpeed); // 최대 속도 제한
    } else if (primaryCar.position.y > targetY) {
      // 위로 이동
      currentSpeed -= acceleration; // 감속
      roadSpeed = Math.max(currentSpeed, minSpeed); // 최소 속도 제한
    } else {
      // 목표에 도달하면 서서히 정지
      currentSpeed *= 0.9; // 점진적 감속 (마찰 효과)
      roadSpeed = Math.abs(currentSpeed) < 0.1 ? 0 : currentSpeed; // 거의 멈추면 정지
    }

    // 차량 포지션을 roadSpeed 속도만큼 이동
    primaryCar.position.y += roadSpeed;
    newCar.position.y += roadSpeed;
  }
  
  let rectWidth = 400; // 사각형 너비
  let rectHeight = height; // 사각형 높이
  let rectX = (width / 2) - (rectWidth / 2); // 사각형 왼쪽 X 좌표
  let rectY = 0; // 사각형 Y 좌표 (맨 위)

  // 좌측 테두리
  line(rectX, rectY, rectX, rectY + rectHeight);

  // 우측 테두리
  line(rectX + rectWidth, rectY, rectX + rectWidth, rectY + rectHeight);
  
}

/**
 * 화면 경계선을 그리기
 */
function drawBoundingBox() {
  noFill(); // 내부를 채우지 않음
  stroke(0); // 경계선 색상 (검은색)
  strokeWeight(4); // 경계선 두께 설정
  rectMode(CORNER); // 사각형 모드를 CORNER로 설정
  rect(2, 2, width - 4, height - 4); // 경계선이 외부로 그려지도록 오프셋 조정
}

// 상태 출력 및 경고

/**
 * 차량이 차선을 벗어났을 때 경고 표시
 * @param {Object} car - 차량 데이터
 */
function displayWarningIfCarOut(car) {
  
  push(); // 이전 상태 저장

  // 경고 메시지 스타일 설정
  textSize(24);
  textAlign(CENTER, CENTER); // 텍스트 중앙 정렬
  noStroke(); // 텍스트에 외곽선 제거

  // 경고 메시지 그리기
  const warningX = width / 2;
  const warningY = 50; // 도로와 겹치지 않는 상단 영역

  if (isCarOutOfLane(car)) {
    fill(255, 0, 0); // 빨간색 텍스트
    text("차선을 벗어났습니다! 패널티 제로: " + (0.1 - primaryCar.penaltyPoints).toFixed(2), warningX, warningY);
    isCarOut = true;
  } else {
    fill(0, 0, 255); // 파란색 텍스트
    text("차량이 차선 안에 있습니다! 패널티 점수: " + (0.1 - primaryCar.penaltyPoints).toFixed(2), warningX, warningY);
    isCarOut = false;
  }

  pop(); // 이전 상태 복원

}

/**
 * 차량 데이터를 화면에 출력
 */
function displayCarData() {
  fill(0, 0, 0, 256); // 검은색(0, 0, 0) + 투명도(128: 반투명)
  textSize(16);
  textStyle(NORMAL); // 글자 스타일을 기본으로 설정 (굵기 줄이기)
  textAlign(LEFT, TOP);

  let logY = 10;
  let logX =  25;
  
  // 단일 차량 정보 출력
  text("Primary Car:", logX , logY);
  logY += 20;
  text(`- Position: (${primaryCar.position.x.toFixed(2)}, ${primaryCar.position.y.toFixed(2)})`, logX, logY);
  logY += 20;
  text(`- Initial Position: (${primaryCar.initialPosition.x.toFixed(2)}, ${primaryCar.initialPosition.y.toFixed(2)})`, logX, logY);
  logY += 20;
  text(`- Speed: ${primaryCar.speed.toFixed(5)}`, logX, logY);
  logY += 20;
  text(`- Direction: ${primaryCar.direction.toFixed(2)} rad`, logX, logY);
  logY += 20;
  text(`- normalizedDirection: ${radiansToClockNumber(primaryCar.direction)} radTime`, logX, logY);
  logY += 20;
  text(`- panalty: ${primaryCar.penaltyPoints } point`, logX, logY);
  logY += 20;

  // 초기 위치와 현재 위치 간 거리 계산 (직접 계산)
  const dx = primaryCar.position.x - primaryCar.initialPosition.x;
  const dy = primaryCar.position.y - primaryCar.initialPosition.y;
  const distanceFromInitial = Math.sqrt(dx * dx + dy * dy);
  
  primaryCar.distanceFromInitial = Math.sqrt(dx * dx + dy * dy); // 계산 결과 저장

  text(`- Distance from Initial Position: ${distanceFromInitial.toFixed(2)} px`, logX, logY);
  logY += 30;

  // vehicleStatus의 숫자 값만 추출
  const numericValues = primaryCarData.vehicleStatus
      ? Object.values(primaryCarData.vehicleStatus).filter(value => typeof value === "number")
      : [];

  // bit_max_nb와 bit_min_nb 계산
  const bit_max_nb = BIT_MAX_NB(numericValues);
  const bit_min_nb = BIT_MIN_NB(numericValues);
  
  primaryCar.bit_max_nb = bit_max_nb
  primaryCar.bit_min_nb = bit_min_nb

  // 배열 데이터 출력
  text("Primary Car Data (Last 15):", logX, logY);
  logY += 20;
  text(`Max Value (bit_max_nb): ${bit_max_nb.toFixed(10)}`, logX, logY);
  logY += 20;
  text(`Min Value (bit_min_nb): ${bit_min_nb.toFixed(10)}`, logX, logY);
  logY += 20;

  // 배열 데이터 출력
  // primaryCarData는 좌측 차량(primary car)의 주행 데이터를 기록한 배열입니다.
  // 각 데이터의 의미를 설명과 함께 화면에 출력합니다.
  const primaryCarDataDescriptions = [
    "헨들링",
    "현재 차량의 속도 (Speed)",
    "현재 차량의 핸들링 (Handling)",
    "현재 차량의 브레이크 상태 (Brake Status)",
    "브레이크 압력 (Brake Pressure)",
    "엔진 출력 (Engine Power)",
    "타이어 상태 (Tire Condition)",
    "차량 안정성 제어 상태 (Stability Control Status)",
    "트랙션 제어 상태 (Traction Control Status)",
    "차량의 연료 상태 (Fuel Level)",
    "현재 가속도 X (Acceleration X)",
    "현재 가속도 Y (Acceleration Y)",
    "센서를 통한 이동 거리 (None)",
    "차량의 정면 센서가 탐지한 newCar까지의 거리.",
    "차량의 후면 센서가 탐지한 newCar까지의 거리.",
    "차량의 우측 센서가 탐지한 newCar까지의 거리.",
    "차량의 좌측 센서가 탐지한 newCar까지의 거리.",
  ];

    if (primaryCarData.vehicleStatus && typeof primaryCarData.vehicleStatus === "object") {
        Object.entries(primaryCarData.vehicleStatus).forEach(([key, value], index) => {
            // 데이터와 설명 출력
            const description = primaryCarDataDescriptions[index] || "알 수 없는 데이터";
            const displayValue = typeof value === "number" ? value.toFixed(2) : value;
            text(`Data ${index + 1}: ${displayValue} (${description})`, logX, logY);
            logY += 20; // 다음 줄로 이동
        });
    } else {
        console.warn("vehicleStatus 데이터가 유효하지 않습니다:", primaryCarData.vehicleStatus);
    }

  
    text(`Data bit_max_nb : ${primaryCarData.bit_max_nb} `, logX, logY);
    logY += 20; // 다음 줄로 이동
    text(`Data bit_min_nb : ${primaryCarData.bit_min_nb} `, logX, logY);
    logY += 20; // 다음 줄로 이동
}

/**
 * 행동 로그를 화면에 출력
 */
function displayActionLog() {
  const logX = width - 200; // 로그의 시작 X 위치
  const logYStart = 50; // 로그의 시작 Y 위치
  const lineHeight = 20; // 로그 항목 간격

  fill(0);
  textSize(14);
  textAlign(LEFT, TOP);

  // 제목 표시
  text("Action Log:", logX, logYStart - 20);

  // 행동 로그 출력
  actionLog.forEach((entry, index) => {
    const logY = logYStart + index * lineHeight;

    // 행동 데이터 출력
    text(
      `Action: ${entry.action}, Reward: ${entry.reward}, Pos: (${entry.position.x}, ${entry.position.y}), Speed: ${entry.speed}, Dir: ${entry.direction}`,
      logX,
      logY
    );
  });
}

/**
 * 학습 상태를 화면에 출력
 */
function displayTrainingStatus() {
  fill(0);
  textSize(16);
  textAlign(RIGHT, TOP);
  text(isTraining ? "Training Active" : "Training Inactive", width - 10, 10);
}

// =====================================
// 5. 센서 데이터 처리 및 계산
// =====================================

/**
 * 센서 거리 계산
 * @param {Object} car - 차량 데이터
 * @param {boolean} isOutOfLane - 차선 이탈 여부
 * @returns {Object} 센서 거리 데이터
 */
function calculateSensorDistances(car, isOutOfLane = true) {
  // 센서 설정
  const sensorRange = 200; // 센서 탐지 범위

  // 초기값을 센서 범위로 설정
  let frontDistance = sensorRange;
  let backDistance = sensorRange;
  let leftDistance = sensorRange;
  let rightDistance = sensorRange;

  // 차량과 newCar 간의 거리 계산
  const dx = newCar.position.x - car.position.x;
  const dy = newCar.position.y - car.position.y;

  // 정면 거리 계산 (newCar가 위쪽에 있을 경우)
  frontDistance = Math.min(
    dy < 0 && Math.abs(dx) <= sensorRange ? Math.abs(dy) : sensorRange,
    sensorRange
  );

  // 후면 거리 계산 (newCar가 아래쪽에 있을 경우)
  if (dy > 0 && Math.abs(dx) <= sensorRange) {
    backDistance = Math.min(backDistance, Math.abs(dy));
  }

  // 좌측 거리 계산 (newCar가 왼쪽에 있을 경우)
  if (dx < 0 && Math.abs(dy) <= sensorRange) {
    leftDistance = Math.min(leftDistance, Math.abs(dx));
  }

  // 우측 거리 계산 (newCar가 오른쪽에 있을 경우)
  if (dx > 0 && Math.abs(dy) <= sensorRange) {
    rightDistance = Math.min(rightDistance, Math.abs(dx));
  }

  //
  
  const normalizedDirection = radiansToClockNumber(car.direction);
  
  // 센서 초기 방향 값 설정
  const sensorDistances = {
    front: frontDistance,
    back: backDistance,
    left: leftDistance,
    right: rightDistance,
  };

  // 차량 방향에 따른 센서 값 조정
  const adjustedDistances = { ...sensorDistances };
  let ai = 0;
  if (normalizedDirection >= 225 && normalizedDirection <= 315) {
    adjustedDistances.front = sensorDistances.front;
    adjustedDistances.back = sensorDistances.back;
    adjustedDistances.left = sensorDistances.right;
    adjustedDistances.right = sensorDistances.left;
    ai = 1; // 위쪽
  } 
  else if (normalizedDirection > 315 || normalizedDirection <= 45 && normalizedDirection >= 0) {
    // 기준에서 0도 회전한 경우 (오른쪽)
    adjustedDistances.front = sensorDistances.right;
    adjustedDistances.back = sensorDistances.left;
    adjustedDistances.left = sensorDistances.back;
    adjustedDistances.right = sensorDistances.front;
    ai = 2; // 오른쪽
  } 
  else if (normalizedDirection <= 240 && normalizedDirection > 145) {
    // 기준에서 0도 회전한 경우 (왼쪽)
    adjustedDistances.front = sensorDistances.left;
    adjustedDistances.back = sensorDistances.right;
    adjustedDistances.left = sensorDistances.front;
    adjustedDistances.right = sensorDistances.back;
    ai = 3; // 왼쪽
  } 
  else if (normalizedDirection > 45 && normalizedDirection <= 145) {
    // 기준에서 270도 회전한 경우 (아래쪽)
    adjustedDistances.front = sensorDistances.back;
    adjustedDistances.back = sensorDistances.front;;
    adjustedDistances.left = sensorDistances.left;
    adjustedDistances.right = sensorDistances.right;
    ai = 4; // 아래쪽
  }

  //console.log('ai', ai);
  //console.log('adjustedDistances', adjustedDistances);
  //console.log('normalizedDirection', normalizedDirection);
  
  adjustedDistances.front = adjustedDistances.front;
  adjustedDistances.back = adjustedDistances.back;
  adjustedDistances.left = adjustedDistances.left;
  adjustedDistances.right = adjustedDistances.right;
  
  // 반환: 방향에 맞춘 센서 값
  return adjustedDistances;
}

/**
 * 방향값을 12시간제 방향 값으로 변환
 * @param {number} radians - 라디안 값
 * @returns {number} 시간 방향 값
 */
function radiansToClockNumber(radians) {
  // 라디안 값을 각도로 변환
  const degrees = (radians * (180 / Math.PI)) % 360; // 라디안 -> 각도
  const normalizedDegrees = (degrees + 360) % 360; // 0~360 범위로 정규화

  // 12시 방향(0도)은 12로 설정
  return normalizedDegrees;
}

/**
 * 차량이 차선을 벗어났는지 확인
 * @param {Object} car - 차량 데이터
 * @returns {boolean} 차선 이탈 여부
 */
function isCarOutOfLane(car) {
  const roadWidth = 200; // 도로 폭
  const laneWidth = roadWidth / 2; // 차선 폭
  const centerX = width / 2; // 도로 중심 X 좌표

  // 차선 경계 계산
  const leftLaneBoundary = centerX - laneWidth; // 왼쪽 차선 경계
  const rightLaneBoundary = centerX + laneWidth; // 오른쪽 차선 경계

  // 차량이 경계를 벗어났는지 확인
  if (car.position.x < leftLaneBoundary || car.position.x > rightLaneBoundary) {
    return true; // 차량이 차선을 벗어남
  }
  return false; // 차량이 차선 안에 있음
}

/**
 * 차량의 현재 차선 상태 반환
 * @param {Object} car - 차량 데이터
 * @returns {string} 차선 상태 ("1차선", "2차선", "차선 밖")
 */
function getCarLaneStatus(car) {
  const roadWidth = 200; // 도로 폭
  const laneWidth = roadWidth / 2; // 차선 폭
  const centerX = width / 2; // 도로 중심 X 좌표

  // 차선 경계 계산
  const leftLaneStart = centerX - roadWidth / 2;
  const leftLaneEnd = centerX - laneWidth;
  const rightLaneStart = centerX;
  const rightLaneEnd = centerX + roadWidth / 2;

  // 차량 위치 확인
  if (car.position.x >= leftLaneStart && car.position.x < leftLaneEnd) {
    return "1차선"; // 차량이 왼쪽 차선에 있음
  } else if (car.position.x >= rightLaneStart && car.position.x <= rightLaneEnd) {
    return "2차선"; // 차량이 오른쪽 차선에 있음
  } else {
    return "차선 밖"; // 차량이 경계를 벗어남
  }
}

// =====================================
// 6. 데이터베이스 처리
// =====================================

/**
 * IndexedDB 열기
 * @returns {Promise<IDBDatabase>} 데이터베이스 객체
 */
function openCarDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(indexDBName, 3); // 데이터베이스 버전 업그레이드

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            if (!db.objectStoreNames.contains("CarData")) {
                const objectStore = db.createObjectStore("CarData", { keyPath: "id", autoIncrement: true });
                objectStore.createIndex("bit_max_nb", "data.bit_max_nb", { unique: false });
                objectStore.createIndex("bit_min_nb", "data.bit_min_nb", { unique: false });

                // 복합 인덱스 생성
                objectStore.createIndex("bit_max_type", ["data.bit_max_nb", "type"], { unique: false });
                objectStore.createIndex("bit_min_type", ["data.bit_min_nb", "type"], { unique: false });
                console.log("복합 인덱스 생성 완료.");
            } else {
                const store = event.target.transaction.objectStore("CarData");
                if (!store.indexNames.contains("bit_max_type")) {
                    store.createIndex("bit_max_type", ["data.bit_max_nb", "type"], { unique: false });
                }
                if (!store.indexNames.contains("bit_min_type")) {
                    store.createIndex("bit_min_type", ["data.bit_min_nb", "type"], { unique: false });
                }
                console.log("기존 Object store에 복합 인덱스 추가 완료.");
            }
        };

        request.onsuccess = (event) => {
            resolve(event.target.result);
        };

        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}

/**
 * 차량 데이터를 IndexedDB에 저장
 * @param {Object} data - 저장할 데이터
 */
async function saveCarSimulationData(data) {
    const db = await openCarDatabase(); // IndexedDB 연결

    return new Promise((resolve, reject) => {
        try {
            const transaction = db.transaction("CarData", "readwrite"); // 트랜잭션 생성
            const store = transaction.objectStore("CarData");

            // 데이터 추가
            const request = store.add(data);

            request.onsuccess = () => {
                //console.log("데이터 저장 성공:", data);
                resolve();
            };

            request.onerror = (error) => {
                //console.error("데이터 저장 실패:", error);
                reject(error);
            };
        } catch (error) {
            console.error("데이터 저장 중 오류 발생:", error);
            reject(error);
        }
    });
}

/**
 * 유사한 차량 데이터를 검색
 * @param {string} type - 데이터 유형
 * @param {number} targetBitMax - 목표 최대 가중치
 * @param {number} targetBitMin - 목표 최소 가중치
 * @param {isHighPenalty} true: 패널티가 높은 상태, false: 패널티가 낮은 상태
 * @returns {Promise<Object>} 검색 결과
 */
async function getSimilarCarSimulationData(type, targetBitMax, targetBitMin, isHighPenalty = true) {
    if (typeof targetBitMax !== "number" || typeof targetBitMin !== "number" || typeof type !== "string") {
        throw new Error("Invalid parameters: bit_max_nb, bit_min_nb must be numbers and type must be a string.");
    }

    const db = await openCarDatabase();
    const transaction = db.transaction("CarData", "readonly");
    const store = transaction.objectStore("CarData");

    const bitMaxTypeIndex = store.index("bit_max_type");
    const bitMinTypeIndex = store.index("bit_min_type");

    // 소수점 자릿수 계산 함수
    function getDecimalPlaces(value) {
        const decimalPart = value.toString().split(".")[1];
        return decimalPart ? decimalPart.length : 0;
    }

    // 범위 계산 함수
    function getRange(value, adjustDecimalPlaces = 0) {
        const decimalValue = new Decimal(value);
        let decimalPlaces = decimalValue.decimalPlaces();
        decimalPlaces = Math.max(0, decimalPlaces + adjustDecimalPlaces);
        const margin = new Decimal(10).pow(-decimalPlaces);
        const lowerBound = decimalValue.minus(margin);
        const upperBound = decimalValue.plus(margin);

        return {
            value: decimalValue.toString(),
            decimalPlaces,
            margin: margin.toString(),
            lowerBound: Number(lowerBound.toString()),
            upperBound: Number(upperBound.toString()),
        };
    }

    // 범위 검색 함수
    async function fetchRangeData(index, lower, upper, type) {
        const range = IDBKeyRange.bound([lower, type], [upper, type]);
        return new Promise((resolve, reject) => {
            const request = index.getAll(range);
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = (event) => reject(event.target.error);
        });
    }

    // 데이터 정규화
    function normalizeData(data) {
        return {
            ...data,
            bit_max_nb: data.data?.bit_max_nb || data.bit_max_nb,
            bit_min_nb: data.data?.bit_min_nb || data.bit_min_nb,
            penaltyPoints: data.data?.penaltyPoints || data.penaltyPoints || 0, // Penalty 값 추가
        };
    }

    let combinedData = [];
    let attempt = 0; // 현재 시도 횟수
    let probabilities;
  
    const maxAttempts = 100; // 최대 시도 횟수
  
    try {
        while (attempt < maxAttempts) {
            //console.log(`Attempt ${attempt + 1}: Expanding range...`);
            
            // targetBitMax와 targetBitMin의 범위 계산
            const bitMaxRange = getRange(targetBitMax, -attempt);
            const bitMinRange = getRange(targetBitMin, -attempt);

            // bit_max_nb 범위 검색
            const bitMaxResults = await fetchRangeData(
                bitMaxTypeIndex,
                bitMaxRange.lowerBound,
                bitMaxRange.upperBound,
                type
            );

            // bit_min_nb 범위 검색
            const bitMinResults = await fetchRangeData(
                bitMinTypeIndex,
                bitMinRange.lowerBound,
                bitMinRange.upperBound,
                type
            );

            combinedData = [...bitMaxResults, ...bitMinResults]
              .map(normalizeData)
              .reduce((unique, item) => {
                if (!unique.some(existing => existing.id === item.id)) {
                  unique.push(item);
                }
                return unique;
              }, [])
              .sort((a, b) => {
                // 우선적으로 penaltyPoints 값을 오름차순으로 정렬
                if (a.penaltyPoints !== b.penaltyPoints) {
                  return a.penaltyPoints - b.penaltyPoints;
                }
                // penaltyPoints 값이 같다면 bit_max_nb를 내림차순으로 정렬
                return b.bit_max_nb - a.bit_max_nb;
              });

            // 패널티 증가 확률 계산
            const totalPenaltyPoints = combinedData.reduce((sum, item) => sum + item.penaltyPoints, 0);
            const penaltyIncreaseProbability = totalPenaltyPoints / (combinedData.length || 1); // 평균 계산
            //console.log(`패널티 증가 확률: ${penaltyIncreaseProbability.toFixed(4)}`);

            // bit_max_nb + bit_min_nb 증가 확률 계산
            const bitIncreaseProbability = combinedData.reduce((sum, item) => {
              const bitSum = item.bit_max_nb + item.bit_min_nb;
              return sum + bitSum;
            }, 0) / (combinedData.length || 1); // 평균 계산
            //console.log(`bit_max_nb + bit_min_nb 증가 확률: ${bitIncreaseProbability.toFixed(4)}`);

            // 결과를 변수로 저장
            probabilities = {
              penaltyIncreaseProbability,
              bitIncreaseProbability
            };

            if (combinedData.length > 0) break; // 데이터가 있으면 종료
            attempt++; // 시도 횟수 증가
        }

        if (attempt === maxAttempts) {
            //console.warn("Maximum attempts reached. Results may still be empty.");
        }

        const targetData = normalizeData({ bit_max_nb: targetBitMax, bit_min_nb: targetBitMin, type });

        const isDuplicate = combinedData.some(
            (item) =>
                item.bit_max_nb === targetData.bit_max_nb &&
                item.bit_min_nb === targetData.bit_min_nb &&
                item.type === targetData.type
        );

        //console.log('isDuplicate', isDuplicate);
        
        return {
            isDuplicate, // 중복 여부 반환
            data: combinedData, // Penalty 기준으로 정렬된 데이터 반환
            probabilities: probabilities,
        };
    } catch (error) {
        throw new Error(`Error fetching similar car data: ${error.message}`);
    }
}

// =====================================
// 7. 이벤트 처리
// =====================================

/**
 * 키보드 입력에 따라 학습 상태 토글
 */
function mousePressed() {
  // 마우스 클릭 시 토글
  isTraining = !isTraining; // 학습 상태 토글
  trainingMode = !trainingMode; // 학습 상태를 true ↔ false로 토글
  console.log(`Training mode: ${isTraining ? "ON" : "OFF"}`); // 상태를 콘솔에 출력
}

/**
 * 마우스 클릭에 따라 학습 상태 토글
 */
function keyPressed() {
  
  // 엔터 키 (13)일 때만 토글
  if (keyCode === 13) {
    isTraining = !isTraining; // 학습 상태 토글
    console.log(`Training mode: ${isTraining ? "ON" : "OFF"}`); // 상태를 콘솔에 출력
  }
  
  // 눌린 키가 스페이스 키인지 확인
  if (keyCode === 32) {
    trainingMode = !trainingMode; // 학습 상태를 true ↔ false로 토글
    console.log(`Training mode: ${trainingMode ? "ON" : "OFF"}`); // 현재 상태를 콘솔에 출력
  }
}

// 방향 처리 함수
/**
 * 방향 정규화 함수
 * - 입력된 방향 값을 -π ~ π 범위로 조정합니다.
 * - 간단한 조건문을 사용하여 한번에 정규화합니다.
 * @param {number} direction - 방향 값 (라디안)
 * @returns {number} - 정규화된 방향 값 (-π ~ π)
 */
function normalizeDirection(direction) {
  const TWO_PI = 2 * Math.PI;
  if (direction > Math.PI) {
    return direction - TWO_PI;
  } else if (direction < -Math.PI) {
    return direction + TWO_PI;
  }
  return direction;
}

// 차량 시각화 함수
// 차량과 센서 데이터를 기반으로 화면에 시각적으로 표시합니다.

/**
 * 차량 그리기 함수
 * - 차량의 위치와 방향에 따라 화면에 그립니다.
 * - 학습 상태에 따라 색상을 변경합니다.
 * - 센서를 기반으로 주변 환경을 시각화합니다.
 * @param {Object} car - 차량 객체
 */

// 초기 변수 선언
let laneOffset = Math.random() < 0.5 ? 50 : -50;
let vibrationLevel = 0; // 진동의 세기 (0: 없음, 1: 약함, 2: 중간, 3: 강함)
let leftIncreaseRate = 0; // 좌측 방향 증가율
let rightIncreaseRate = 0; // 우측 방향 증가율
let speedChangeRate = 0; // 속도 변화율

function drawPrimaryCar(car, newCar) {
  push();
  translate(car.position.x, car.position.y); // 차량 위치로 이동
  rotate(car.direction); // 차량 방향에 맞춰 회전

  // 센서 그리기
  //const distances = calculateSensorDistances(car); // 센서 거리 계산
  //drawSensors(car, distances); // 센서 시각화
  
  // 차량 회전
  const vehicleRotation = 0;

  // 센서 탐지 각도와 애니메이션 요소
  const sensorAngle = PI / 6;
  const animatedRangeFactor = 10 * sin(0 * 0.05);
  const slowMotionFactor = 0.5;
  
  // 센서 그리기
  const distances = calculateSensorDistances(car); // 센서 거리 계산
  
  // popularity 생성
  const popularity = calculatePopularity(distances);

  // 첫 번째 센서 시각화
  drawSensors(distances, vehicleRotation, sensorAngle, animatedRangeFactor, slowMotionFactor);

  // 두 번째 인기 센서 시각화
  const SensorsdashedPoints = drawPopularSensors(distances, vehicleRotation, sensorAngle, animatedRangeFactor, slowMotionFactor);
  
  // 차량 센서 데이터를 기반으로 popularity 계산
  function calculatePopularity(sensorData) {
    return {
      front: sensorData.front > 50 ? 3 : 1,
      back: sensorData.back > 30 ? 2 : 1,
      left: sensorData.left > 20 ? 4 : 1,
      right: sensorData.right > 10 ? 1 : 0,
    };
  }
  
  // 차량 본체 색상 설정
  if (isTraining) {
    fill(0, 255, 255); // 학습 중: 시안
  } else if (car.speed > 8) {
    fill(75, 0, 130); // 속도가 빠를 때: 인디고
  } else if (car.penaltyPoints < -5) {
    fill(255, 105, 180); // 패널티 점수 매우 낮을 때: 핫핑크
  } else {
    fill(123, 104, 238); // 기본 상태: 미디엄 슬레이트 블루
  }
  rectMode(CENTER);
  rect(0, 0, 60, 30, 10); // 차량 본체
  
  pop();
  if (isTraining) {
    // 범위 내에 있는지 확인하는 변수
    const isWithinBounds = primaryCar.position.x >= (width / 2) - 100 && primaryCar.position.x <= (width / 2) + 100;

    // 목표 설정
    let classSpeed = Number($('.nb-dependency-speed').text());
    let classDirection = Number($('.machine-learning-direction').text());
    const goalY = 50; // Topmost coordinate of the second lane
    let laneBoundsX = (width / 2) + laneOffset;

    // 차선 위치 결정
    if (newCar.position.y > height - 75) {
        laneBoundsX = (width / 2) + (Math.random() < 0.5 ? 50 : -50);
        console.log('laneBoundsX', laneBoundsX);
    }
    indexLine = navigateToSingleGoal(primaryCar, laneBoundsX, goalY, classSpeed, classDirection);

    // 센서 거리 총합 계산
    const distances = calculateSensorDistances(primaryCar);
    const totalDistance = distances.front + distances.back + distances.left + distances.right;

    // 패널티 계산
    const collisionWeight = 0.5;    // 충돌 가중치
    const distanceWeight = 0.3;     // 거리 가중치
    const outOfBoundsWeight = 0.2;  // 차선 이탈 가중치

    const collisionPenalty = collisionDetected ? collisionWeight : 0;
    const normalizedDistance = Math.max(0, Math.min((800 - totalDistance) / 800, 1)); // 거리 정규화
    const distancePenalty = normalizedDistance * distanceWeight;
    const outOfBoundsPenalty = isCarOut ? outOfBoundsWeight : 0;

    let totalPenalty = collisionPenalty + distancePenalty + outOfBoundsPenalty;
    totalPenalty = Math.min(totalPenalty, 1); // 패널티는 1 이하로 제한

    // 패널티 점수 업데이트
    primaryCar.penaltyPoints = 
        (indexLine / 10000) +  // 선과의 연관된 기본 패널티
        totalPenalty -         // 패널티 조정 값
        (totalDistance / 10000); // 거리가 멀수록 패널티 감소

    // 패널티 점수가 0보다 작아지지 않도록 제한
    primaryCar.penaltyPoints = Math.max(primaryCar.penaltyPoints, 0);

    if (dashedCenters.length > 0) {
        if (classSpeed === 0) classSpeed = 5;

        // 방향 계산 및 정규화
        const angle = -Math.PI / 2; // 초기값
        const normalizedAngle = (angle + 2 * Math.PI) % (2 * Math.PI); // 0 ~ 2π 사이로 정규화
        indexangleDifference = determineDirection(Number($('.nb-dependency-direction').text()), normalizedAngle);

        // 벌점 기반 조향 보정값 설정
        const carPoints = Math.max(Number($('.penalty-increase-probability').text()) / 100, 0);

        if (totalDistance < 750 || (collisionDetected && isWithinBounds)) {
            if (indexangleDifference === "좌측") {
                indexangleDifference = "예측 조향은 좌측 방향입니다.";
                leftIncreaseRate += vibrationLevel === 0 ? carPoints : -carPoints * 2;
                classDirection += leftIncreaseRate;
            } else if (indexangleDifference === "우측") {
                indexangleDifference = "예측 조향은 우측 방향입니다.";
                rightIncreaseRate += vibrationLevel === 0 ? -carPoints : carPoints * 2;
                classDirection += rightIncreaseRate;
            }
            classDirection = (classDirection + 2 * Math.PI) % (2 * Math.PI); // 정규화

            // 충돌 감지 시 속도 감소
            if (collisionDetected && classSpeed > 0) {
                indexangleDifference += "::속도를 줄이세요.";
                speedChangeRate += vibrationLevel === 0 ? carPoints : -carPoints * 2;
                classSpeed += speedChangeRate;
                $('.nb-dependency-speed').text(classSpeed);
            } else {
              classSpeed = 1;
            }

            vibrationLevel = vibrationLevel > 0 ? 0 : vibrationLevel + 1;

            // 차량 이동
            moveCarAlongDashedPath(car, classSpeed, classDirection);
        } else {
            // 변수 초기화를 직접 반영
            leftIncreaseRate = 0;
            rightIncreaseRate = 0;
            speedChangeRate = 0;

            // 충돌 감지 시 속도 감소
            if (collisionDetected && classSpeed > 0) {
                indexangleDifference += "속도를 줄이세요.";
                classSpeed -= 0.1;
                $('.nb-dependency-speed').text(classSpeed);
            } else {
              classSpeed = 1;
            }

            // 조향 비활성화 및 차량 이동
            moveCarAlongDashedPath(car, classSpeed, false);
        }
      } else {
          console.log("차량이 모든 점선 중심을 따라 이동 완료.");
      }
  }
}

function determineDirection(currentAngle, straightAngle = 4.7) {
  // 기준 각도를 기준으로 방향 판별
  if (currentAngle > straightAngle) {
    return '우측'; // 직진 기준 우측
  } else if (currentAngle < straightAngle) {
    return '좌측'; // 직진 기준 좌측
  } else {
    return '직진'; // 기준 각도와 동일
  }
}

// 예제 사용
const currentAngle = 5.2; // 현재 각도 (예: 5.2 라디안)
const direction = determineDirection(currentAngle);
console.log(direction); // 결과: '우측'

function moveCarAlongDashedPath(car, speed, classDirection = false) {
  if (dashedCenters.length === 0) {
    console.log("점선 중심 좌표가 없습니다.");
    return;
  }

  // 현재 차량 위치에서 가장 가까운 점선 중심 좌표를 찾음
  let closestIndex = -1;
  let minDistance = Infinity;
  dashedCenters.forEach((center, index) => {
    const dx = center.x - car.position.x;
    const dy = center.y - car.position.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < minDistance) {
      minDistance = distance;
      closestIndex = index;
    }
  });

  if (closestIndex === -1) {
    console.log("가장 가까운 점선 중심을 찾을 수 없습니다.");
    return;
  }

  // 다음 목표 점선 중심 설정
  const targetCenter = dashedCenters[closestIndex];

  // 차량 방향 계산 (목표 점선 중심으로 회전)
  const dx = targetCenter.x - car.position.x;
  const dy = targetCenter.y - car.position.y;
  const targetDirection = Math.atan2(dy, dx);

  // 회전 각도 제한 설정
  const maxTurnAngle = Math.PI / 30; // 최대 회전 각도
  const turnSpeed = Math.PI / 240; // 방향 변경 속도 (느리게 회전)
  let angleDifference;

  if (classDirection !== false) {
    // classDirection이 존재하면 그 값을 기준으로 회전
    angleDifference = normalizeDirection(classDirection - car.direction);
  } else {
    // 목표 점선 중심 방향으로 회전
    angleDifference = normalizeDirection(targetDirection - car.direction);
  }

  // 짧은 회전 경로 선택
  angleDifference = ((angleDifference + Math.PI) % (2 * Math.PI)) - Math.PI;

  // 방향 변경
  if (Math.abs(angleDifference) > turnSpeed) {
    car.direction += Math.sign(angleDifference) * turnSpeed;
  } else {
    car.direction += angleDifference;
  }

  // 방향 값 정상화 (0~2π)
  car.direction = (car.direction + 2 * Math.PI) % (2 * Math.PI);

  // 차량 이동
  car.position.x += speed * Math.cos(car.direction);
  car.position.y += speed * Math.sin(car.direction);
  car.speed = speed;

  // 차량이 목표 중심에 가까워지면 다음 중심으로 이동
  if (minDistance < speed) {
    dashedCenters.splice(closestIndex, 1); // 해당 점선 중심 제거
  }
}

  /**
  * 주행 모션으로 센서를 시각화
  * @param {string} color - 센서 색상 (RGB)
  * @param {number} range - 센서 거리
  * @param {number} rotation - 센서 회전 각도
  * @param {number} sensorAngle - 센서 탐지 각도
  * @param {number} animatedRangeFactor - 동적 반경 변화량
  * @param {number} slowMotionFactor - 슬로우 모션 적용 비율
  * @param {number} motionFactor - 주행 모션 적용 비율
  */

  function drawSensorFan(color, range, rotation, sensorAngle, animatedRangeFactor, slowMotionFactor, lineCount) {
    noFill();

    // 투명도 추가 (RGBA 형식으로 색상 처리)
    const alpha = 0.05; // 투명도 값 (0~1)
    const [r, g, b] = color.match(/\d+/g); // RGB 값 추출
    stroke(`rgba(${r},${g},${b},${alpha})`);

    // 동적 반경 계산
    const dynamicRange = Math.max(10, range - animatedRangeFactor * slowMotionFactor); // 최소 반경 설정

    // 라인 개수에 따라 탐지 각도를 나누는 간격 계산
    const step = sensorAngle / Math.max(1, lineCount); // 최소 1개의 라인 보장

    const coordinates = []; // 끝점 좌표를 저장할 배열

    // 탐지 각도에 따라 라인 그리기
    for (let angle = -sensorAngle / 2; angle <= sensorAngle / 2; angle += step) {
      const currentRotation = rotation + angle;

      // 끝점 (조정된 거리와 회전 각도에 따라)
      const endX = dynamicRange * Math.cos(currentRotation);
      const endY = dynamicRange * Math.sin(currentRotation);

      // 좌표 저장
      coordinates.push({ x: endX, y: endY });

      // 라인 그리기
      line(0, 0, endX, endY);
    }

    // 좌표 반환
    return coordinates;
  }

  /**
       * 가장 인기 있는 센서를 주행 모션으로 시각화
       * @param {Object} distances - 센서 거리
       * @param {Object} popularity - 센서 인기 데이터
       */
  function drawPopularSensors(distances, vehicleRotation, sensorAngle, animatedRangeFactor, slowMotionFactor) {
    const sensorData = [];

    function calculateAndDrawSensor(sensorName, color, range, rotation, sensorAngle, animatedRangeFactor, slowMotionFactor, lineCount) {
      const coordinates = drawSensorFan(
        color,               // 센서 색상
        range,               // 센서 탐지 거리
        rotation,            // 센서 회전 각도
        sensorAngle,         // 센서 탐지 각도
        animatedRangeFactor, // 동적 반경 변화량
        slowMotionFactor,    // 슬로우 모션 비율
        lineCount            // 라인 밀도
      );

      // 각 센서 데이터 저장
      sensorData.push({
        sensor: sensorName,
        coordinates: coordinates,
      });
    }

    // 정면 센서
    calculateAndDrawSensor(
      'front',
      'rgba(255, 0, 0, 0.6)',
      distances.front,
      vehicleRotation,
      sensorAngle,
      animatedRangeFactor,
      slowMotionFactor,
      25
    );

    // 후면 센서
    calculateAndDrawSensor(
      'back',
      'rgba(0, 255, 0, 0.6)',
      distances.back,
      vehicleRotation + Math.PI,
      sensorAngle,
      animatedRangeFactor,
      slowMotionFactor,
      10
    );

    // 좌측 센서
    calculateAndDrawSensor(
      'left',
      'rgba(0, 0, 255, 0.6)',
      distances.left,
      vehicleRotation + Math.PI / 2,
      sensorAngle,
      animatedRangeFactor,
      slowMotionFactor,
      10
    );

    // 우측 센서
    calculateAndDrawSensor(
      'right',
      'rgba(255, 255, 0, 0.6)',
      distances.right,
      vehicleRotation - Math.PI / 2,
      sensorAngle,
      animatedRangeFactor,
      slowMotionFactor,
      10
    );

    return sensorData; // 센서 데이터를 반환
  }

  /**
       * 센서 그리기 함수
       * @param {string} color - 센서 색상 (RGB)
       * @param {number} range - 센서 거리
       * @param {number} rotation - 센서 회전 각도
       * @param {number} sensorAngle - 센서 탐지 각도
       * @param {number} animatedRangeFactor - 동적 반경 변화량
       * @param {number} slowMotionFactor - 슬로우 모션 적용 비율
       */
  function drawSensor(color, range, rotation, sensorAngle, animatedRangeFactor, slowMotionFactor) {
    noFill();
    stroke(color); // 센서 색상
    const adjustedRange = Math.max(0, range - animatedRangeFactor * slowMotionFactor); // 조정된 반경
    arc(
      0, 0,
      adjustedRange * 2, adjustedRange * 2,
      rotation - sensorAngle / 2,
      rotation + sensorAngle / 2
    );
  }

  /**
       * 센서를 시각화
       * @param {Object} car - 차량 데이터
       * @param {Object} distances - 센서 거리
       */
  function drawSensors(distances, vehicleRotation, sensorAngle, animatedRangeFactor, slowMotionFactor) {
    // 정면 센서
    drawSensor('rgba(255, 0, 0, 0.6)', distances.front, vehicleRotation, sensorAngle, animatedRangeFactor, slowMotionFactor);

    // 후면 센서
    drawSensor('rgba(0, 255, 0, 0.6)', distances.back, vehicleRotation + PI, sensorAngle, animatedRangeFactor, slowMotionFactor);

    // 좌측 센서
    drawSensor('rgba(0, 0, 255, 0.6)', distances.left, vehicleRotation + HALF_PI, sensorAngle, animatedRangeFactor, slowMotionFactor);

    // 우측 센서
    drawSensor('rgba(255, 255, 0, 0.6)', distances.right, vehicleRotation - HALF_PI, sensorAngle, animatedRangeFactor, slowMotionFactor);
  }


  // 로그 관리 함수
  // 콘솔 로그를 정리하고 주기적으로 현재 상태를 출력합니다.

  /**
       * 콘솔 초기화 함수
       * - 콘솔 로그를 초기화하고 메시지를 출력합니다.
       */
  function clearConsole() {
    console.clear(); // 콘솔 초기화
    console.log("콘솔이 초기화되었습니다!"); // 초기화 메시지 출력
  }

  /**
       * 로그 출력 주기 함수
       * - 25초마다 콘솔을 초기화하고 현재 시간을 출력합니다.
       */
  setInterval(() => {
    clearConsole();
    const timestamp = new Date().toISOString(); // 현재 시간 생성
    console.log(`현재 시간: ${timestamp} - 5초마다 실행되는 로그`);
  }, 600000); // 25초마다 실행
