# Duxcycler-prototype
Duxcycler prototype software for Real-Time multiplex PCR

<br><br>

# Notice

- 220706 세미나 도중 PCR protocol에 shot 기능 요구사항을 반영하기 위한 branch

    - PCR Protocol 도중 `next_label` 이 "GOTO" 이고,  현재 진행중인 Protocol line이 10 초 남았을 때 shot을 찍음
        - 해당 기능 삭제
            - 기존 shot 기능 에서 필요했던 "PCR protocol 각 line의 time이 >15sec" 인 기능 제거
        - Duxcycler Thermal cycler firmware 에서 State "PAUSE" 추가 필요
        - PCR protocol 텍스트 파일에서 shot을 명시하는 column 추가
    - shot_thread 및 filter wheel homing 시 thread 사용한다는 것도 생각 해야함

<br><br>

# TODO

1. [x] `./pcr/protocol` 에서 "load" 시 ~~column이 shot인~~ label 이 "SHOT" 인 line 인식
    - [x] protocol line time 이 >15sec 이어야 하는 logic 제거

2. [x] `./pcr/task.py` 의 `check_shot()` logic 수정
    - ./pcr/task.py 에 Command.RESUME을 추가하기 위한  `cur_loop`, `pre_label`, `cur_label` flag 변수 추가

3. [x] shot Thread 및 homing thread 키는 것 생각...(shot logic 수정 하라는 뜻)
    - 불필요
    - 다만 `./pcr/optic/shot_thread` 에서 thread event 기반 loop 문은 그대로 유지(GUI 멈춤 현상과 관련)

4. [x] Firmware 에서 "PAUSE" state 추가
    - 해당 과정에서 state diagram 재설계 및 검토 필요 -> firmware 쪽에서 state PAUSE 를 추가하지 않고 기존의 기능 `isTimeInfinite` 을 사용하여 구현 -> 해당 내용으로 state diagram 재설계


5. [x] `./pcr/task.py`의 `check_status()` logic 수정
    - `Command.RESUME` 관련하여 command setting 부분 수정

6. [ ] shot 기능 테스트
    - `Command.RESUME` send -> 완료
    - 형광 이미지 shot 및 저장, 이미지 분석 -> 완료
    - 위 3번 관련 UI 멈추는 현상 -> 테스트중

7. [ ] 정리 및 문서화
    - 진행중