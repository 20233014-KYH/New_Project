package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.SituationRule;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SituationRuleRepository extends JpaRepository<SituationRule, String> {
}
