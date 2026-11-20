package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.SituationPick;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SituationPickRepository extends JpaRepository<SituationPick, String> {
}
