import { useEffect, useMemo, useState } from 'react'
import styled, { createGlobalStyle, css, keyframes } from 'styled-components'
import bgImage from './background/bg.png'
import tigerImage from './character/tiger/tiger.png'
import cocoImage from './character/coco/coco.png'

const EMPLOYEES = [
  {
    id: 'tiger',
    name: '티거',
    animal: 'Tiger',
    avatar: tigerImage,
    title: 'Planning Agent',
    color: '#8e5a16',
    desk: { x: 19, y: 83 },
    meetingSpot: { x: 73, y: 23 },
  },
  {
    id: 'coco',
    name: '코코',
    animal: 'Coco',
    avatar: cocoImage,
    title: 'Execution Agent',
    color: '#c56d1d',
    desk: { x: 61, y: 83 },
    meetingSpot: { x: 82, y: 28 },
  },
]

const STATUS_COPY = {
  idle: {
    title: '직원들이 각자 자리에서 대기 중입니다.',
    description: '회의실을 누르면 모두 모여 브리핑을 시작합니다.',
  },
  gathering: {
    title: '회의실로 이동 중입니다.',
    description: '직원들이 회의실로 모이고 있어요.',
  },
  meeting: {
    title: '브리핑을 기다리고 있습니다.',
    description: '업무를 입력하면 메인 에이전트가 분배합니다.',
  },
  evaluating: {
    title: '메인 에이전트가 평가 중입니다.',
    description: '업무를 분석해 직원별 작업으로 나누고 있어요.',
  },
  working: {
    title: '직원들이 각자 자리에서 작업 중입니다.',
    description: '배정된 업무가 직원 정보 창에 표시됩니다.',
  },
}

const PHASE_LABELS = {
  idle: '대기 중',
  gathering: '회의실 이동',
  meeting: '브리핑 대기',
  evaluating: '업무 분석',
  working: '작업 중',
}

const STATUS_COLORS = {
  gathering: '#4e89df',
  meeting: '#f1b54a',
  evaluating: '#b468df',
  working: '#5ebd72',
}

const EVALUATION_DELAY = 1800
const GATHERING_DELAY = 1400
const MOVEMENT_TICK = 40

const Background = styled.div`
  position: fixed;
  inset: 0;

  background-image: url(${bgImage});
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;

  background-color: black;
  z-index: -1;
`;

const ListButton = styled.div`
  position: absolute;
  bottom: 20px;
  right: 20px;

  width: 35px;
  height: 35px;
  background: white;

  border-radius: 50px;
`;

const ListModal = styled.div`
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);

  align-items: center;
  justify-content: center;
  text-align: center;

  width: calc(50%);
  height: auto;
  background-color: white;

  border-radius: 5px;
`

const Font = styled.p`
 &.title{
  font: 25px 'arial';
  margin: 0;
  padding: 10px;
 } 

 &.middle_title{
  font: 20px 'arial';
 }

 &.small_title{
  font: 18px 'arial';
 }

 &.text{
  font: 15px 'arial';
 }

 &.small_text{
  font: 13px 'arial';
 }

`

const AgentList = styled.div`
  display: flex;
  flex-direction: row;
  width: calc(90%);
  height: auto;
  background-color: #f7d487;
  border-radius: 5px;
`

const AgentImg = styled.img`
  width: 50%;
  height: 50%;
  object-fit: contain;
  background-color: white;
  margin: 10px;
  border-radius: 5px;
`

const AgentInfo = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: start;
  padding-left: 10px;
`

const App = () => {
  const [listOpen, setListOpen] = useState(false);

  return (
    <Background>
      <ListButton onClick={() => setListOpen(!listOpen)} />

      {listOpen && (
        <ListModal>
          <Font className='title'>직원 정보</Font>
          <AgentList>
            <AgentImg src = {cocoImage}/>
            <AgentInfo>
              <Font className='middle_title'>이름 : 코코</Font>
              <Font className='text'>직급 : 사장</Font>
              <Font className='small_text'>Head Agent로 지시를 하위 agent에게 전달</Font>
            </AgentInfo>
          </AgentList>
        </ListModal>
      )}
    </Background>
  );
};

export default App;
