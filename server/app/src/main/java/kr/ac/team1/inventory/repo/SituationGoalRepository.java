package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.SituationGoal;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SituationGoalRepository extends JpaRepository<SituationGoal, String> {
}
