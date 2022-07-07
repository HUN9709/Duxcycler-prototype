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

1. [ ] `./pcr/protocol` 에서 "load" 시 column이 shot인 line 인식
    - protocol line time 이 >15sec 이어야 하는 logic 제거

2. [ ] `./pcr/task.py` 의 `check_shot()` logic 수정

3. [ ] shot Thread 및 homing thread 키는 것 생각...(shot logic 수정 하라는 뜻)

4. [ ] Firmware 에서 "PAUSE" state 추가
    - 해당 과정에서 state diagram 재설계 및 검토 필요

5. [ ] `./pcr/task.py`의 `check_status()` logic 수정

6. [ ] shot 기능 테스트
    - test list 추가 필요!

7. [ ] 정리 및 문서화